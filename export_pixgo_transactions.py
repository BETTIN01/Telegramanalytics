import argparse
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from config import DATABASE_PATH
from app.services import pixgo_service as pixgo

try:
    import psycopg2
except Exception:
    psycopg2 = None


def load_accounts():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    row = cur.execute("SELECT value FROM settings WHERE key='pixgo_accounts'").fetchone()
    conn.close()
    if not row or not row[0]:
        return []
    try:
        items = json.loads(row[0])
    except Exception:
        return []
    accounts = []
    for item in items:
        if not isinstance(item, dict):
            continue
        accounts.append({
            "id": str(item.get("id") or "").strip(),
            "name": str(item.get("name") or "").strip(),
            "api_key": str(item.get("api_key") or "").strip(),
            "is_default": bool(item.get("is_default")),
        })
    return accounts


def resolve_accounts(accounts, selector):
    selector = (selector or "all").strip().lower()
    if selector in {"all", "*"}:
        return [acc for acc in accounts if acc.get("api_key")]
    matched = []
    for acc in accounts:
        if selector in {acc.get("id", "").lower(), acc.get("name", "").lower()} and acc.get("api_key"):
            matched.append(acc)
    return matched


def load_ids_from_db(account_names):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if account_names:
        placeholders = ",".join("?" for _ in account_names)
        rows = cur.execute(
            f"SELECT DISTINCT payment_id FROM finance_transactions WHERE provider='pixgo' AND provider_account IN ({placeholders}) ORDER BY created_at DESC",
            list(account_names),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT DISTINCT payment_id FROM finance_transactions WHERE provider='pixgo' ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [str(row["payment_id"]).strip() for row in rows if row["payment_id"]]


def load_bot_payments():
    if psycopg2 is None:
        return []
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="vip",
        user="postgres",
        password="postgres",
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT external_id, chat_id, payment_id, plano_key, amount, status, created_at, updated_at
        FROM pagamentos
        WHERE payment_id IS NOT NULL AND payment_id <> ''
        ORDER BY created_at ASC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    payments = []
    for row in rows:
        payments.append({
            "external_id": str(row[0] or "").strip(),
            "chat_id": row[1],
            "payment_id": str(row[2] or "").strip(),
            "plano_key": str(row[3] or "").strip(),
            "amount": row[4],
            "status": str(row[5] or "").strip(),
            "created_at": row[6].isoformat(sep=" ") if row[6] else "",
            "updated_at": row[7].isoformat(sep=" ") if row[7] else "",
        })
    return payments


def load_ids_from_file(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        parsed = json.loads(text)
        if isinstance(parsed, list):
            values = parsed
        elif isinstance(parsed, dict):
            values = parsed.get("payment_ids") or parsed.get("ids") or parsed.get("payments") or []
        else:
            values = []
        ids = []
        for item in values:
            if isinstance(item, dict):
                value = item.get("payment_id") or item.get("id")
            else:
                value = item
            if value:
                ids.append(str(value).strip())
        return ids

    ids = []
    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames:
        for row in reader:
            value = row.get("payment_id") or row.get("id")
            if value:
                ids.append(str(value).strip())
        if ids:
            return ids
    for line in text.splitlines():
        line = line.strip()
        if line:
            ids.append(line)
    return ids


def first_value(data, *paths):
    for path in paths:
        cur = data
        ok = True
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if ok and cur not in (None, "", []):
            return cur
    return None


def build_record(account, payment_id, details, status):
    merged = {}
    if isinstance(details, dict):
        merged.update(details)
    if isinstance(status, dict):
        merged.update(status)

    return {
        "account": account.get("name") or account.get("id") or "",
        "payment_id": first_value(merged, ("payment_id",), ("id",), ("data", "payment_id"), ("data", "id")) or payment_id,
        "external_id": first_value(merged, ("external_id",), ("data", "external_id")) or "",
        "status": first_value(merged, ("status",), ("payment_status",), ("data", "status")) or "",
        "amount": first_value(merged, ("amount",), ("value",), ("data", "amount")) or "",
        "description": first_value(merged, ("description",), ("data", "description")) or "",
        "customer_name": first_value(merged, ("customer_name",), ("payer_name",), ("customer", "name"), ("data", "customer_name"), ("data", "payer_name")) or "",
        "customer_cpf": first_value(merged, ("customer_cpf",), ("payer_cpf",), ("customer", "cpf"), ("data", "customer_cpf"), ("data", "payer_cpf")) or "",
        "customer_email": first_value(merged, ("customer_email",), ("payer_email",), ("customer", "email"), ("data", "customer_email"), ("data", "payer_email")) or "",
        "customer_phone": first_value(merged, ("customer_phone",), ("payer_phone",), ("customer", "phone"), ("data", "customer_phone"), ("data", "payer_phone")) or "",
        "qr_code": first_value(merged, ("qr_code",), ("pix_code",), ("copy_paste",), ("pix_copia_cola",), ("data", "qr_code")) or "",
        "qr_image_url": first_value(merged, ("qr_image_url",), ("image_url",), ("data", "qr_image_url"), ("data", "image_url")) or "",
        "checkout_id": first_value(merged, ("checkout_id",), ("data", "checkout_id")) or "",
        "expires_at": first_value(merged, ("expires_at",), ("expiration_date",), ("data", "expires_at")) or "",
        "completed_at": first_value(merged, ("completed_at",), ("data", "completed_at")) or "",
        "raw_json": json.dumps(merged, ensure_ascii=False),
    }


def build_local_bot_record(payment):
    return {
        "account": "",
        "payment_id": payment.get("payment_id", ""),
        "external_id": payment.get("external_id", ""),
        "status": payment.get("status", "") or "local_only",
        "amount": float(payment.get("amount") or 0) if payment.get("amount") not in (None, "") else "",
        "description": payment.get("plano_key", ""),
        "customer_name": "",
        "customer_cpf": "",
        "customer_email": "",
        "customer_phone": "",
        "qr_code": "",
        "qr_image_url": "",
        "checkout_id": "",
        "expires_at": "",
        "completed_at": "",
        "created_at": payment.get("created_at", ""),
        "updated_at": payment.get("updated_at", ""),
        "raw_json": json.dumps(payment, ensure_ascii=False, default=str),
    }


def export_rows(rows, fmt, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    fieldnames = [
        "account",
        "payment_id",
        "external_id",
        "status",
        "amount",
        "description",
        "customer_name",
        "customer_cpf",
        "customer_email",
        "customer_phone",
        "checkout_id",
        "expires_at",
        "completed_at",
        "created_at",
        "updated_at",
        "qr_code",
        "qr_image_url",
        "raw_json",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description="Exporta transacoes conhecidas da PIXGO em CSV ou JSON. Observacao: como a PIXGO nao expoe listagem publica confiavel, este script consulta payment_ids conhecidos."
    )
    parser.add_argument("--account", default="all", help="Conta configurada no painel: vibratura, velatura ou all")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Formato de saida")
    parser.add_argument("--output", help="Arquivo de saida. Padrao: exports/pixgo_export_<data>.<ext>")
    parser.add_argument("--ids-file", help="Arquivo .txt/.csv/.json com payment_ids")
    parser.add_argument("--payment-id", action="append", default=[], help="Payment ID individual. Pode repetir varias vezes.")
    parser.add_argument("--source", choices=["all-known", "local-db", "bot-db"], default="all-known", help="Origem dos payment_ids conhecidos")
    parser.add_argument("--list-accounts", action="store_true", help="Lista as contas PIXGO configuradas no painel e sai.")
    args = parser.parse_args()

    accounts = load_accounts()
    if args.list_accounts:
        for acc in accounts:
            mark = " (default)" if acc.get("is_default") else ""
            print(f"{acc.get('name')} [{acc.get('id')}] {mark}")
        return

    selected_accounts = resolve_accounts(accounts, args.account)
    if not selected_accounts:
        raise SystemExit("Nenhuma conta PIXGO configurada encontrada para esse seletor.")

    bot_payments = load_bot_payments() if args.source in {"all-known", "bot-db"} else []
    payment_ids = []
    if args.ids_file:
        payment_ids.extend(load_ids_from_file(args.ids_file))
    payment_ids.extend(args.payment_id or [])
    if not payment_ids:
        if args.source in {"all-known", "local-db"}:
            payment_ids.extend(load_ids_from_db([acc.get("name") for acc in selected_accounts if args.account != "all"]))
        if args.source in {"all-known", "bot-db"}:
            payment_ids.extend([item.get("payment_id") for item in bot_payments])
    payment_ids = [pid for pid in dict.fromkeys(pid.strip() for pid in payment_ids if pid and pid.strip())]
    if not payment_ids:
        raise SystemExit("Nenhum payment_id conhecido foi encontrado. Informe --ids-file ou --payment-id.")

    bot_lookup = {item.get("payment_id"): item for item in bot_payments if item.get("payment_id")}
    rows = []
    failures = []
    for payment_id in payment_ids:
        found = False
        for account in selected_accounts:
            try:
                details = pixgo.get_payment_details(account["api_key"], payment_id)
                status = pixgo.get_payment_status(account["api_key"], payment_id)
                rows.append(build_record(account, payment_id, details, status))
                found = True
                break
            except pixgo.PixGoError as err:
                failures.append({
                    "payment_id": payment_id,
                    "account": account.get("name") or account.get("id"),
                    "message": err.message,
                })
        if not found:
            local_payment = bot_lookup.get(payment_id)
            if local_payment:
                rows.append(build_local_bot_record(local_payment))
                print(f"[local] {payment_id}")
            else:
                print(f"[nao encontrado] {payment_id}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or f"exports/pixgo_export_{timestamp}.{args.format}"
    export_rows(rows, args.format, output_path)

    print(f"Exportadas {len(rows)} transacoes para {output_path}")
    if failures:
        print(f"Falhas registradas: {len(failures)}")
        preview = failures[:10]
        for item in preview:
            print(f" - {item['payment_id']} @ {item['account']}: {item['message']}")


if __name__ == "__main__":
    main()
