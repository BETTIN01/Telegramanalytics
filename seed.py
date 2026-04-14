import sys, random
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).parent))

from app.services.db_service import init_db, record_event

CHAT_ID    = -1009876543210
CHAT_TITLE = "Grupo Teste"
USERS = [(101,"marcos_dev"),(102,"ana_silva"),(103,"pedro_net"),
         (104,"julia_ux"),(105,"carlos_db"),(106,"fernanda_qa")]

def run():
    Path("database").mkdir(exist_ok=True)
    init_db()
    base = datetime.utcnow() - timedelta(days=30)
    n = 0
    for day in range(30):
        for _ in range(random.randint(3, 18)):
            uid, uname = random.choice(USERS)
            record_event(uid, uname, CHAT_ID, CHAT_TITLE, "join"); n += 1
        for _ in range(random.randint(0, 4)):
            uid, uname = random.choice(USERS)
            record_event(uid, uname, CHAT_ID, CHAT_TITLE, "leave"); n += 1
    print(f"✅ {n} eventos inseridos para \"{CHAT_TITLE}\"")
    print("   Rode: python main.py  →  http://localhost:5000")

if __name__ == "__main__": run()