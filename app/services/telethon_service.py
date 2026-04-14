import asyncio
import logging
import threading
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsSearch
from app.services import db_service as db

log = logging.getLogger(__name__)

API_ID   = 37981545
API_HASH = 'd236cdf31a23d72e88726efc4497a7a0'
SESSION  = 'database/telethon_session'


def sync_all_members(chat_id):
    result = [None]
    exc    = [None]

    def _run():
        async def _inner():
            async with TelegramClient(SESSION, API_ID, API_HASH) as client:
                entity = await client.get_entity(chat_id)
                all_members = []
                offset = 0
                limit  = 200
                while True:
                    participants = await client(GetParticipantsRequest(
                        entity,
                        ChannelParticipantsSearch(''),
                        offset=offset,
                        limit=limit,
                        hash=0
                    ))
                    if not participants.users:
                        break
                    all_members.extend(participants.users)
                    offset += len(participants.users)
                    if offset >= participants.count:
                        break

                admins_ids = set()
                try:
                    admin_participants = await client(GetParticipantsRequest(
                        entity,
                        ChannelParticipantsAdmins(),
                        offset=0,
                        limit=200,
                        hash=0
                    ))
                    admins_ids = {user.id for user in admin_participants.users}
                except Exception:
                    pass

                db.replace_member_admins(chat_id, admins_ids)

                for m in all_members:
                    if m.bot:
                        continue
                    full  = (m.first_name or '') + (' ' + m.last_name if m.last_name else '')
                    uname = m.username or str(m.id)
                    db.upsert_member(chat_id, m.id, uname, full.strip(), is_admin=m.id in admins_ids)

                result[0] = (True, f'Sincronizados {len(all_members)} membros de {participants.count} total.')

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_inner())
            loop.close()
        except Exception as e:
            exc[0] = e

    t = threading.Thread(target=_run)
    t.start()
    t.join(timeout=60)

    if exc[0]:
        return False, str(exc[0])
    if result[0] is None:
        return False, 'Timeout na sincronização.'
    return result[0]
