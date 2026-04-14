import logging, os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")

from config import PORT, get_token
from app.services.db_service  import init_db
from app.services.bot_service import start_bot
from app import create_app

def main():
    Path("database").mkdir(exist_ok=True)
    print("Inicializando banco...")
    init_db()

    token = get_token()
    if token:
        print("Iniciando bot Telegram...")
        ok, msg = start_bot(token)
        print("   ->", msg)
    else:
        print("Token nao configurado. Acesse Configuracoes no dashboard.")

    app = create_app()
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    import threading, time, sqlite3
    from app.services.telethon_service import sync_all_members
    from app.services.report_service import dispatch_due_reports

    def auto_sync():
        time.sleep(60)
        while True:
            try:
                conn = sqlite3.connect('database/analytics.db')
                cur  = conn.cursor()
                cur.execute('SELECT chat_id FROM groups')
                groups = [r[0] for r in cur.fetchall()]
                conn.close()
                for cid in groups:
                    ok, msg = sync_all_members(cid)
                    print(f'[AUTO-SYNC] {cid}: {msg}')
            except Exception as e:
                print(f'[AUTO-SYNC] Erro: {e}')
            time.sleep(1800)

    threading.Thread(target=auto_sync, daemon=True, name='auto-sync').start()
    print('Auto-sync ativado (30min)')

    def auto_reports():
        time.sleep(20)
        while True:
            try:
                dispatch_due_reports()
            except Exception as e:
                print(f'[AUTO-REPORTS] Erro: {e}')
            time.sleep(60)

    threading.Thread(target=auto_reports, daemon=True, name='auto-reports').start()
    print('Auto-reports ativado (1min)')

    print(f"\nDashboard -> http://localhost:{PORT}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
