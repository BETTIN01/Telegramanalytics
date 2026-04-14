import asyncio
import logging
import threading
import time
import urllib.request
import urllib.error
from telegram import Update
from telegram.ext import Application, MessageHandler, ChatMemberHandler, filters, ContextTypes
from app.services import db_service as db
from app.services.db_service import record_event

log = logging.getLogger(__name__)

# Deduplicação: evita registrar o mesmo evento 2x em 10 segundos
_event_cache = {}
_cache_lock  = threading.Lock()

def _is_duplicate(user_id, event_type):
    key = (user_id, event_type)
    now = time.time()
    with _cache_lock:
        last = _event_cache.get(key, 0)
        if now - last < 10:
            return True
        _event_cache[key] = now
        return False
_lock = threading.Lock()
_start_lock = threading.Lock()
_loop = None
_thread = None
_app = None
_running = False


def _clear_telegram_session(token):
    url = "https://api.telegram.org/bot" + token + "/deleteWebhook?drop_pending_updates=true"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            log.info("deleteWebhook -> %s", resp.read().decode())
    except urllib.error.URLError as e:
        log.warning("deleteWebhook falhou: %s", e)
    time.sleep(4)


async def _on_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    chat_id = msg.chat.id
    chat_title = msg.chat.title or str(chat_id)
    if msg.new_chat_members:
        for m in msg.new_chat_members:
            if m.is_bot:
                continue
            name = m.username or m.first_name or str(m.id)
            full = (m.first_name or "") + (" " + m.last_name if m.last_name else "")
            record_event(m.id, name, chat_id, chat_title, "join", full.strip())
            db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
            log.info("[JOIN] @%s -> %s", name, chat_title)
    if msg.left_chat_member:
        m = msg.left_chat_member
        if not m.is_bot:
            name = m.username or m.first_name or str(m.id)
            full = (m.first_name or "") + (" " + m.last_name if m.last_name else "")
            record_event(m.id, name, chat_id, chat_title, "leave", full.strip())
            db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
            log.info("[LEAVE] @%s -> %s", name, chat_title)




async def _on_chat_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    chat_id    = cmu.chat.id
    chat_title = cmu.chat.title or str(chat_id)
    m          = cmu.new_chat_member.user
    old_status = cmu.old_chat_member.status
    new_status = cmu.new_chat_member.status
    print(f"[CMU-DEBUG] @{cmu.new_chat_member.user.username or cmu.new_chat_member.user.id}: {old_status} -> {new_status}", flush=True)
    if m.is_bot:
        return
    name       = m.username or m.first_name or str(m.id)
    full       = (m.first_name or "") + (" " + m.last_name if m.last_name else "")
    chat_title = chat_title or str(chat_id)
    if not name or name == "None":
        return
    JOINED  = {"member", "administrator", "creator"}
    LEFT    = {"left", "kicked"}
    was_in  = old_status in JOINED
    now_in  = new_status in JOINED
    was_out = old_status in LEFT
    now_out = new_status in LEFT

    if was_out and now_in:
        if _is_duplicate(m.id, "join"): return
        db.upsert_member(chat_id, m.id, name, full.strip(), is_admin=False)
        record_event(m.id, name, chat_id, chat_title, "join", full.strip())
        log.info("[JOIN-CMU] @%s -> %s", name, chat_title)
    elif was_in and now_out:
        if _is_duplicate(m.id, "leave"): return
        record_event(m.id, name, chat_id, chat_title, "leave", full.strip())
        db.remove_member(chat_id, m.id)
        log.info("[LEAVE-CMU] @%s -> %s", name, chat_title)
    else:
        log.debug("[SKIP-CMU] %s->%s @%s", old_status, new_status, name)

def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def stop_bot():
    global _app, _loop, _thread, _running
    with _lock:
        if not _running or _app is None or _loop is None:
            _running = False
            return

        async def _shutdown():
            global _app, _running
            try:
                if _app.updater.running:
                    await _app.updater.stop()
                if _app.running:
                    await _app.stop()
                await _app.shutdown()
            except Exception as e:
                log.warning("Erro no shutdown: %s", e)
            finally:
                _app = None
                _running = False

        try:
            asyncio.run_coroutine_threadsafe(_shutdown(), _loop).result(timeout=10)
        except Exception as e:
            log.warning("Timeout no shutdown: %s", e)
            _running = False
            _app = None
        try:
            _loop.call_soon_threadsafe(_loop.stop)
        except Exception:
            pass
        if _thread and _thread.is_alive():
            _thread.join(timeout=5)
        _loop = None
        _thread = None


def start_bot(token):
    global _app, _loop, _thread, _running
    if not _start_lock.acquire(blocking=False):
        return False, "Bot ja esta sendo iniciado, aguarde."
    try:
        token = (token or "").strip()
        if not token:
            return False, "Token vazio."
        if _running:
            stop_bot()
        _clear_telegram_session(token)
        with _lock:
            try:
                loop = asyncio.new_event_loop()
                thread = threading.Thread(
                    target=_run_loop,
                    args=(loop,),
                    daemon=True,
                    name="tg-bot-loop",
                )
                thread.start()
                _loop = loop
                _thread = thread

                async def _boot():
                    global _app, _running
                    application = Application.builder().token(token).build()
                    application.add_handler(
                        ChatMemberHandler(_on_chat_member, ChatMemberHandler.CHAT_MEMBER)
                    )
                    await application.initialize()
                    await application.updater.start_polling(
                        poll_interval=2,
                        timeout=20,
                        drop_pending_updates=True,
                        allowed_updates=["message", "chat_member"],
                    )
                    await application.start()
                    _app = application
                    _running = True
                    log.info("Bot online (polling)")

                asyncio.run_coroutine_threadsafe(_boot(), loop).result(timeout=25)
                return True, "Bot iniciado com sucesso!"
            except Exception as e:
                _running = False
                _app = None
                log.error("Erro ao iniciar bot: %s", e)
                return False, "Erro: " + str(e)
    finally:
        _start_lock.release()


def is_running():
    return _running


async def sync_members(chat_id):
    if _app is None:
        return False, "Bot nao esta rodando."
    try:
        count  = await _app.bot.get_chat_member_count(chat_id)
        admins = await _app.bot.get_chat_administrators(chat_id)
        admin_ids = [a.user.id for a in admins]
        db.replace_member_admins(chat_id, admin_ids)
        for a in admins:
            u     = a.user
            full  = (u.first_name or "") + (" " + u.last_name if u.last_name else "")
            uname = u.username or str(u.id)
            db.upsert_member(chat_id, u.id, uname, full.strip(), is_admin=True)
        return True, "Sincronizados " + str(len(admins)) + " admins. Total no grupo: " + str(count)
    except Exception as e:
        return False, str(e)


def sync_members_sync(chat_id):
    if _loop is None or not _running:
        return False, "Bot nao esta rodando."
    fut = asyncio.run_coroutine_threadsafe(sync_members(chat_id), _loop)
    return fut.result(timeout=15)
