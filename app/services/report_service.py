import csv
import io
import smtplib
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from uuid import uuid4

from config import get_token
from app.services import analytics_service as an
from app.services import db_service as db


PAID_STATUSES = {"paid", "approved", "completed", "success", "succeeded", "delivered", "concluido"}
DEFAULT_EXPORT_SECTIONS = {
    "overview": True,
    "charts": True,
    "events": True,
    "members": True,
    "finance": True,
    "campaigns": True,
    "pixel": True,
}


def _group_title(chat_id):
    for group in db.get_all_groups():
        try:
            if int(group.get("chat_id")) == int(chat_id):
                return group.get("chat_title") or str(chat_id)
        except Exception:
            continue
    return str(chat_id)


def _slug(value):
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value or ""))
    clean = "-".join(part for part in clean.split("-") if part)
    return clean or "grupo"


def _filename(chat_id, ext):
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"painel-hot_{_slug(_group_title(chat_id))}_{chat_id}_{stamp}.{ext}"


def _to_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def _to_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _to_dt(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", ""))
    except Exception:
        return None


def _currency(value):
    return f"R$ {_to_float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _percent(value):
    return f"{_to_float(value):.1f}%"


def _trend(current, previous):
    current = _to_float(current)
    previous = _to_float(previous)
    if current > previous:
        return "Alta"
    if current < previous:
        return "Queda"
    return "Estavel"


def _month_label(key):
    names = {"01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr", "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago", "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"}
    text = str(key or "")
    if len(text) == 7 and "-" in text:
        year, month = text.split("-", 1)
        return f"{names.get(month, month)}/{year[-2:]}"
    return text or "-"


def _normalize_monthly(rows):
    normalized = []
    for row in rows or []:
        normalized.append({
            "month": row.get("month"),
            "label": _month_label(row.get("month")),
            "joins": _to_int(row.get("joins")),
            "leaves": _to_int(row.get("leaves")),
            "net": _to_int(row.get("net")),
        })
    return normalized


def _event_comparison(rows):
    monthly = _normalize_monthly(rows)
    current = monthly[-1] if monthly else {"label": "-", "joins": 0, "leaves": 0, "net": 0}
    previous = monthly[-2] if len(monthly) > 1 else {"label": "-", "joins": 0, "leaves": 0, "net": 0}
    return {
        "current": current,
        "previous": previous,
        "joins_delta": current["joins"] - previous["joins"],
        "leaves_delta": current["leaves"] - previous["leaves"],
        "net_delta": current["net"] - previous["net"],
    }


def _finance_payload(chat_id):
    metrics = db.get_finance_home_metrics(chat_id)
    transactions = db.get_finance_transactions(chat_id, limit=250)
    monthly = {}
    recent = []

    for tx in transactions:
        recent.append({
            "payment_id": tx.get("payment_id") or "-",
            "customer_name": tx.get("customer_name") or "Nao informado",
            "provider_account": tx.get("provider_account") or tx.get("provider") or "-",
            "amount": _to_float(tx.get("amount")),
            "status": str(tx.get("status") or "-"),
            "updated_at": tx.get("completed_at") or tx.get("updated_at") or tx.get("created_at") or "-",
        })
        stamp = _to_dt(tx.get("completed_at") or tx.get("updated_at") or tx.get("created_at"))
        if not stamp:
            continue
        key = stamp.strftime("%Y-%m")
        bucket = monthly.setdefault(key, {"label": _month_label(key), "transactions": 0, "approved": 0, "revenue": 0.0})
        bucket["transactions"] += 1
        if str(tx.get("status") or "").strip().lower() in PAID_STATUSES:
            bucket["approved"] += 1
            bucket["revenue"] += _to_float(tx.get("amount"))

    monthly_rows = [monthly[key] for key in sorted(monthly.keys())][-6:]
    current = monthly_rows[-1] if monthly_rows else {"label": "-", "transactions": 0, "approved": 0, "revenue": 0.0}
    previous = monthly_rows[-2] if len(monthly_rows) > 1 else {"label": "-", "transactions": 0, "approved": 0, "revenue": 0.0}
    return {
        "metrics": metrics,
        "recent": recent[:8],
        "monthly": monthly_rows,
        "comparison": {
            "current": current,
            "previous": previous,
            "transactions_delta": current["transactions"] - previous["transactions"],
            "approved_delta": current["approved"] - previous["approved"],
            "revenue_delta": current["revenue"] - previous["revenue"],
        },
    }


def _pixel_payload():
    pixel_id = db.get_setting("meta_pixel_id", "").strip()
    access_token = db.get_setting("meta_access_token", "").strip()
    ad_account_id = db.get_setting("meta_ad_account_id", "").strip()
    dataset_id = db.get_setting("meta_dataset_id", "").strip()
    test_event_code = db.get_setting("meta_test_event_code", "").strip()
    ready = bool(pixel_id and access_token and ad_account_id)
    return {
        "ready": ready,
        "pixel_id": pixel_id,
        "ad_account_id": ad_account_id,
        "dataset_id": dataset_id,
        "test_event_code": test_event_code,
        "token_preview": (access_token[:8] + "..." + access_token[-4:]) if len(access_token) > 14 else ("configurado" if access_token else ""),
        "campaigns_running": 0,
        "campaigns_paused": 0,
        "clicks_today": 0,
        "leads_today": 0,
        "next_step": "Conectar a Marketing API da Meta." if ready else "Salvar Pixel ID, Access Token e Ad Account ID.",
    }


def _report_payload(chat_id):
    summary = db.get_summary(chat_id)
    timeseries = db.get_timeseries(chat_id)
    hourly = db.get_hourly(chat_id)
    weekday = db.get_weekday(chat_id)
    total_joins = summary.get("total_joins", 0) or 0
    total_leaves = summary.get("total_leaves", 0) or 0
    monthly = an.monthly_stats(timeseries)[-6:]
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "generated_at_file": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "group_title": _group_title(chat_id),
        "summary": summary,
        "weekly": an.weekly_stats(timeseries)[-8:],
        "monthly": _normalize_monthly(monthly),
        "insights": an.generate_insights(timeseries, hourly, weekday, summary),
        "top_members": db.get_top_members(chat_id, limit=8),
        "recent_events": db.get_recent(chat_id, limit=8),
        "peak_hour": an.peak_hour(hourly),
        "peak_day": an.peak_weekday(weekday),
        "members": db.get_member_count(chat_id),
        "total_joins": total_joins,
        "total_leaves": total_leaves,
        "net_growth": total_joins - total_leaves,
        "churn_rate": an.churn_rate(total_joins, total_leaves),
        "event_comparison": _event_comparison(monthly),
        "finance": _finance_payload(chat_id),
        "pixel": _pixel_payload(),
    }


def build_csv_export(chat_id):
    payload = _report_payload(chat_id)
    event_compare = payload["event_comparison"]
    finance = payload["finance"]
    pixel = payload["pixel"]
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Painel HOT", payload["group_title"]])
    writer.writerow(["Gerado em", payload["generated_at_file"]])
    writer.writerow(["Escopo", "Overview + Financeiro + PIXEL"])
    writer.writerow([])

    writer.writerow(["Resumo executivo"])
    writer.writerow(["Indicador", "Valor"])
    writer.writerow(["Entradas totais", payload["total_joins"]])
    writer.writerow(["Saidas totais", payload["total_leaves"]])
    writer.writerow(["Crescimento liquido", payload["net_growth"]])
    writer.writerow(["Churn", _percent(payload["churn_rate"])])
    writer.writerow(["Membros na base", _to_int(payload["members"].get("total"))])
    writer.writerow(["Admins", _to_int(payload["members"].get("admins"))])
    writer.writerow(["Pico de hora", f"{payload['peak_hour'].get('hour', '-') }h"])
    writer.writerow(["Melhor dia", payload["peak_day"].get("weekday", "-")])
    writer.writerow([])

    writer.writerow(["Comparacao com o ultimo mes"])
    writer.writerow(["Metrica", event_compare["previous"]["label"], event_compare["current"]["label"], "Delta", "Tendencia"])
    writer.writerow(["Entradas", event_compare["previous"]["joins"], event_compare["current"]["joins"], event_compare["joins_delta"], _trend(event_compare["current"]["joins"], event_compare["previous"]["joins"])])
    writer.writerow(["Saidas", event_compare["previous"]["leaves"], event_compare["current"]["leaves"], event_compare["leaves_delta"], _trend(event_compare["current"]["leaves"], event_compare["previous"]["leaves"])])
    writer.writerow(["Liquido", event_compare["previous"]["net"], event_compare["current"]["net"], event_compare["net_delta"], _trend(event_compare["current"]["net"], event_compare["previous"]["net"])])
    writer.writerow([])

    writer.writerow(["Evolucao semanal"])
    writer.writerow(["Semana", "Entradas", "Saidas", "Liquido"])
    for row in payload["weekly"]:
        writer.writerow([row["week"], row["joins"], row["leaves"], row["net"]])
    writer.writerow([])

    writer.writerow(["Evolucao mensal"])
    writer.writerow(["Mes", "Entradas", "Saidas", "Liquido"])
    for row in payload["monthly"]:
        writer.writerow([row["label"], row["joins"], row["leaves"], row["net"]])
    writer.writerow([])

    writer.writerow(["Financeiro PIXGO"])
    writer.writerow(["Indicador", "Valor"])
    writer.writerow(["Faturamento total", _currency(finance["metrics"]["total_revenue"])])
    writer.writerow(["Transacoes ultimas 24h", finance["metrics"]["transactions_last_24h"]])
    writer.writerow(["Aprovadas ultimas 24h", finance["metrics"]["approved_last_24h"]])
    writer.writerow(["Aprovadas na semana", finance["metrics"]["approved_this_week"]])
    writer.writerow([])

    writer.writerow(["Comparacao financeira mensal"])
    writer.writerow(["Metrica", finance["comparison"]["previous"]["label"], finance["comparison"]["current"]["label"], "Delta", "Tendencia"])
    writer.writerow(["Receita", _currency(finance["comparison"]["previous"]["revenue"]), _currency(finance["comparison"]["current"]["revenue"]), _currency(finance["comparison"]["revenue_delta"]), _trend(finance["comparison"]["current"]["revenue"], finance["comparison"]["previous"]["revenue"])])
    writer.writerow(["Aprovadas", finance["comparison"]["previous"]["approved"], finance["comparison"]["current"]["approved"], finance["comparison"]["approved_delta"], _trend(finance["comparison"]["current"]["approved"], finance["comparison"]["previous"]["approved"])])
    writer.writerow(["Transacoes", finance["comparison"]["previous"]["transactions"], finance["comparison"]["current"]["transactions"], finance["comparison"]["transactions_delta"], _trend(finance["comparison"]["current"]["transactions"], finance["comparison"]["previous"]["transactions"])])
    writer.writerow([])

    writer.writerow(["Financeiro por mes"])
    writer.writerow(["Mes", "Transacoes", "Aprovadas", "Receita"])
    for row in finance["monthly"]:
        writer.writerow([row["label"], row["transactions"], row["approved"], _currency(row["revenue"])])
    writer.writerow([])

    writer.writerow(["Ultimas transacoes"])
    writer.writerow(["Pagamento", "Cliente", "Conta", "Valor", "Status", "Atualizado"])
    for row in finance["recent"]:
        writer.writerow([row["payment_id"], row["customer_name"], row["provider_account"], _currency(row["amount"]), row["status"], row["updated_at"]])
    writer.writerow([])

    writer.writerow(["Tela PIXEL / Meta"])
    writer.writerow(["Campo", "Valor"])
    writer.writerow(["Status", "Conectado" if pixel["ready"] else "Aguardando configuracao"])
    writer.writerow(["Pixel ID", pixel["pixel_id"] or "Nao informado"])
    writer.writerow(["Ad Account ID", pixel["ad_account_id"] or "Nao informado"])
    writer.writerow(["Dataset ID", pixel["dataset_id"] or "Nao informado"])
    writer.writerow(["Test Event Code", pixel["test_event_code"] or "Nao informado"])
    writer.writerow(["Token", pixel["token_preview"] or "Nao configurado"])
    writer.writerow(["Campanhas rodando", pixel["campaigns_running"]])
    writer.writerow(["Campanhas pausadas", pixel["campaigns_paused"]])
    writer.writerow(["Cliques hoje", pixel["clicks_today"]])
    writer.writerow(["Leads hoje", pixel["leads_today"]])
    writer.writerow(["Proximo passo", pixel["next_step"]])
    writer.writerow([])

    writer.writerow(["Top membros"])
    writer.writerow(["Username", "Entradas", "Saidas", "Eventos"])
    for row in payload["top_members"]:
        writer.writerow([row.get("username") or "-", row.get("joins") or 0, row.get("leaves") or 0, row.get("total_events") or 0])
    writer.writerow([])

    writer.writerow(["Insights"])
    writer.writerow(["Resumo"])
    for insight in payload["insights"]:
        writer.writerow([insight])

    return _filename(chat_id, "csv"), ("\ufeff" + buf.getvalue()).encode("utf-8")


def build_pdf_export(chat_id):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.graphics.shapes import Drawing, Line, Rect, String
    except ImportError as exc:
        raise RuntimeError("reportlab not installed") from exc

    def metric_row(items, widths):
        table = Table([items], colWidths=widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#1e3a8a")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#1e293b")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        return table

    def chart(title, rows, keys, colors_hex):
        drawing = Drawing(520, 210)
        drawing.add(String(0, 192, title, fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
        if not rows:
            drawing.add(String(0, 120, "Sem dados suficientes para o grafico.", fontSize=10, fillColor=colors.HexColor("#64748b")))
            return drawing
        left, bottom, width, height = 38, 34, 450, 120
        drawing.add(Rect(left, bottom, width, height, strokeColor=colors.HexColor("#cbd5e1"), fillColor=None))
        values = []
        for row in rows:
            for key in keys:
                values.append(_to_float(row.get(key)))
        peak = max(values) if values else 1
        if peak <= 0:
            peak = 1
        step = width / max(len(rows) - 1, 1)
        for idx, row in enumerate(rows):
            x = left + (idx * step)
            drawing.add(String(x - 10, bottom - 14, str(row.get("label") or row.get("week") or "")[:8], fontSize=8, fillColor=colors.HexColor("#64748b")))
        for idx, key in enumerate(keys):
            previous = None
            color = colors.HexColor(colors_hex[idx % len(colors_hex)])
            for pos, row in enumerate(rows):
                value = _to_float(row.get(key))
                x = left + (pos * step)
                y = bottom + (value / peak) * height
                drawing.add(Rect(x - 2, y - 2, 4, 4, strokeColor=color, fillColor=color))
                if previous:
                    drawing.add(Line(previous[0], previous[1], x, y, strokeColor=color, strokeWidth=2))
                previous = (x, y)
        return drawing

    payload = _report_payload(chat_id)
    finance = payload["finance"]
    pixel = payload["pixel"]
    compare = payload["event_comparison"]

    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=26, rightMargin=26, topMargin=28, bottomMargin=22)
    story = []

    def add_table(title, headers, rows, widths, header_color):
        story.append(Paragraph(title, styles["Heading2"]))
        table = Table([headers] + rows, colWidths=widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d5dbe5")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(table)
        story.append(Spacer(1, 14))

    story.append(Paragraph(f"Painel HOT - {payload['group_title']}", styles["Title"]))
    story.append(Paragraph(f"Relatorio executivo gerado em {payload['generated_at']}", styles["Normal"]))
    story.append(Paragraph("Atualizado para Overview, Financeiro PIXGO e nova tela PIXEL.", styles["BodyText"]))
    story.append(Spacer(1, 14))

    cards = []
    for label, value in [("Entradas", str(payload["total_joins"])), ("Saidas", str(payload["total_leaves"])), ("Liquido", str(payload["net_growth"])), ("Churn", _percent(payload["churn_rate"]))]:
        cards.append(Paragraph(f"<font color='#93c5fd' size='9'><b>{label}</b></font><br/><font color='white' size='18'><b>{value}</b></font>", styles["BodyText"]))
    story.append(metric_row(cards, [120, 120, 120, 120]))
    story.append(Spacer(1, 16))

    add_table(
        "Comparacao com o ultimo mes",
        ["Metrica", compare["previous"]["label"], compare["current"]["label"], "Delta", "Tendencia"],
        [
            ["Entradas", compare["previous"]["joins"], compare["current"]["joins"], compare["joins_delta"], _trend(compare["current"]["joins"], compare["previous"]["joins"])],
            ["Saidas", compare["previous"]["leaves"], compare["current"]["leaves"], compare["leaves_delta"], _trend(compare["current"]["leaves"], compare["previous"]["leaves"])],
            ["Liquido", compare["previous"]["net"], compare["current"]["net"], compare["net_delta"], _trend(compare["current"]["net"], compare["previous"]["net"])],
        ],
        [120, 95, 95, 80, 90],
        colors.HexColor("#1d4ed8"),
    )

    story.append(chart("Evolucao mensal do grupo", payload["monthly"], ["joins", "leaves", "net"], ["#2563eb", "#ef4444", "#0f766e"]))
    story.append(Spacer(1, 14))
    story.append(chart("Ritmo semanal", payload["weekly"], ["joins", "leaves"], ["#7c3aed", "#f97316"]))
    story.append(Spacer(1, 14))

    add_table(
        "Resumo operacional",
        ["Indicador", "Valor"],
        [
            ["Membros na base", _to_int(payload["members"].get("total"))],
            ["Admins", _to_int(payload["members"].get("admins"))],
            ["Pico de hora", f"{payload['peak_hour'].get('hour', '-') }h"],
            ["Melhor dia", payload["peak_day"].get("weekday", "-")],
        ],
        [210, 270],
        colors.HexColor("#0f172a"),
    )

    add_table(
        "Top membros",
        ["Username", "Entradas", "Saidas", "Eventos"],
        [[row.get("username") or "-", row.get("joins") or 0, row.get("leaves") or 0, row.get("total_events") or 0] for row in payload["top_members"]] or [["-", 0, 0, 0]],
        [210, 85, 85, 85],
        colors.HexColor("#0f766e"),
    )

    story.append(PageBreak())
    story.append(Paragraph("Financeiro PIXGO", styles["Title"]))
    story.append(Spacer(1, 10))

    finance_cards = []
    for label, value in [("Faturamento total", _currency(finance["metrics"]["total_revenue"])), ("Transacoes 24h", str(finance["metrics"]["transactions_last_24h"])), ("Aprovadas 24h", str(finance["metrics"]["approved_last_24h"])), ("Aprovadas semana", str(finance["metrics"]["approved_this_week"]))]:
        finance_cards.append(Paragraph(f"<font color='#a7f3d0' size='9'><b>{label}</b></font><br/><font color='white' size='16'><b>{value}</b></font>", styles["BodyText"]))
    story.append(metric_row(finance_cards, [120, 120, 120, 120]))
    story.append(Spacer(1, 16))

    add_table(
        "Comparacao financeira mensal",
        ["Metrica", finance["comparison"]["previous"]["label"], finance["comparison"]["current"]["label"], "Delta", "Tendencia"],
        [
            ["Receita", _currency(finance["comparison"]["previous"]["revenue"]), _currency(finance["comparison"]["current"]["revenue"]), _currency(finance["comparison"]["revenue_delta"]), _trend(finance["comparison"]["current"]["revenue"], finance["comparison"]["previous"]["revenue"])],
            ["Aprovadas", finance["comparison"]["previous"]["approved"], finance["comparison"]["current"]["approved"], finance["comparison"]["approved_delta"], _trend(finance["comparison"]["current"]["approved"], finance["comparison"]["previous"]["approved"])],
            ["Transacoes", finance["comparison"]["previous"]["transactions"], finance["comparison"]["current"]["transactions"], finance["comparison"]["transactions_delta"], _trend(finance["comparison"]["current"]["transactions"], finance["comparison"]["previous"]["transactions"])],
        ],
        [120, 110, 110, 90, 80],
        colors.HexColor("#0f766e"),
    )

    story.append(chart("Receita e aprovacoes por mes", finance["monthly"], ["revenue", "approved"], ["#16a34a", "#0ea5e9"]))
    story.append(Spacer(1, 14))

    add_table(
        "Ultimas transacoes",
        ["Pagamento", "Cliente", "Conta", "Valor", "Status"],
        [[row["payment_id"][:28], row["customer_name"], row["provider_account"], _currency(row["amount"]), row["status"]] for row in finance["recent"]] or [["-", "-", "-", _currency(0), "-"]],
        [150, 125, 90, 70, 85],
        colors.HexColor("#1f2937"),
    )

    story.append(PageBreak())
    story.append(Paragraph("Tela PIXEL / Meta", styles["Title"]))
    story.append(Spacer(1, 10))

    pixel_cards = []
    for label, value in [("Status", "Conectado" if pixel["ready"] else "Aguardando"), ("Campanhas rodando", str(pixel["campaigns_running"])), ("Cliques hoje", str(pixel["clicks_today"])), ("Leads hoje", str(pixel["leads_today"]))]:
        pixel_cards.append(Paragraph(f"<font color='#fbcfe8' size='9'><b>{label}</b></font><br/><font color='white' size='16'><b>{value}</b></font>", styles["BodyText"]))
    story.append(metric_row(pixel_cards, [120, 120, 120, 120]))
    story.append(Spacer(1, 16))

    add_table(
        "Status da integracao Meta",
        ["Campo", "Valor"],
        [
            ["Pixel ID", pixel["pixel_id"] or "Nao informado"],
            ["Ad Account ID", pixel["ad_account_id"] or "Nao informado"],
            ["Dataset ID", pixel["dataset_id"] or "Nao informado"],
            ["Test Event Code", pixel["test_event_code"] or "Nao informado"],
            ["Token", pixel["token_preview"] or "Nao configurado"],
            ["Proximo passo", pixel["next_step"]],
        ],
        [170, 310],
        colors.HexColor("#7c3aed"),
    )

    story.append(Paragraph("Insights principais", styles["Heading2"]))
    for insight in payload["insights"]:
        story.append(Paragraph(f"- {insight}", styles["BodyText"]))
        story.append(Spacer(1, 4))

    doc.build(story)
    buf.seek(0)
    return _filename(chat_id, "pdf"), buf.getvalue()


def _telegram_multipart(fields, file_field, filename, content, mime_type):
    boundary = f"----PainelHot{uuid4().hex}"
    body = io.BytesIO()
    for key, value in fields.items():
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.write(str(value).encode("utf-8"))
        body.write(b"\r\n")
    body.write(f"--{boundary}\r\n".encode("utf-8"))
    body.write(f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8"))
    body.write(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
    body.write(content)
    body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, body.getvalue()


def send_report_telegram(destination, filename, content, mime_type, caption):
    token = get_token().strip()
    if not token:
        raise RuntimeError("Telegram bot token not configured.")
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    boundary, payload = _telegram_multipart({"chat_id": destination, "caption": caption}, "document", filename, content, mime_type)
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def send_report_email(destination, filename, content, mime_type, subject):
    host = db.get_setting("smtp_host", "").strip()
    port = int(db.get_setting("smtp_port", "587") or 587)
    username = db.get_setting("smtp_username", "").strip()
    password = db.get_setting("smtp_password", "").strip()
    sender = db.get_setting("smtp_sender", "").strip() or username
    use_tls = db.get_setting("smtp_tls", "1").strip() != "0"
    if not host or not sender:
        raise RuntimeError("SMTP settings are incomplete.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = destination
    msg.set_content("Painel HOT weekly report attached.")
    maintype, subtype = mime_type.split("/", 1)
    msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if use_tls:
            smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(msg)


def dispatch_due_reports():
    now = datetime.now()
    due = db.get_due_scheduled_reports(now.weekday(), now.hour, now.minute)
    for item in due:
        try:
            if item["format"] == "pdf":
                filename, content = build_pdf_export(item["chat_id"])
                mime_type = "application/pdf"
            else:
                filename, content = build_csv_export(item["chat_id"])
                mime_type = "text/csv"
            caption = f"Painel HOT - {_group_title(item['chat_id'])}"
            subject = f"Painel HOT weekly report - {_group_title(item['chat_id'])}"
            if item["delivery_type"] == "telegram":
                send_report_telegram(item["destination"], filename, content, mime_type, caption)
            else:
                send_report_email(item["destination"], filename, content, mime_type, subject)
            db.mark_scheduled_report_sent(item["id"], "")
        except Exception as exc:
            db.mark_scheduled_report_error(item["id"], str(exc))


def _parse_date(value):
    return _to_dt(value)


def _format_range_label(start_date, end_date):
    if start_date and end_date:
        return f"{start_date.strftime('%d/%m/%Y')} ate {end_date.strftime('%d/%m/%Y')}"
    if start_date:
        return f"A partir de {start_date.strftime('%d/%m/%Y')}"
    if end_date:
        return f"Ate {end_date.strftime('%d/%m/%Y')}"
    return "Todo o historico disponivel"


def _normalize_export_options(options=None):
    raw = dict(options or {})
    sections = dict(DEFAULT_EXPORT_SECTIONS)
    if isinstance(raw.get("sections"), dict):
        for key in sections:
            if key in raw["sections"]:
                sections[key] = bool(raw["sections"][key])
    start_date = _parse_date(raw.get("start_date"))
    end_date = _parse_date(raw.get("end_date"))
    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date
    return {
        "start_date": start_date,
        "end_date": end_date,
        "sections": sections,
        "range_label": _format_range_label(start_date, end_date),
    }


def _build_date_filters(column, start_date=None, end_date=None):
    clauses = []
    params = []
    if start_date:
        clauses.append(f"date({column}) >= ?")
        params.append(start_date.strftime("%Y-%m-%d"))
    if end_date:
        clauses.append(f"date({column}) <= ?")
        params.append(end_date.strftime("%Y-%m-%d"))
    return clauses, params


def _event_payload_filtered(chat_id, options):
    conn = db.get_connection()
    clauses = ["chat_id=?"]
    params = [chat_id]
    extra_clauses, extra_params = _build_date_filters("created_at", options["start_date"], options["end_date"])
    clauses.extend(extra_clauses)
    params.extend(extra_params)
    where = " AND ".join(clauses)

    summary = dict(conn.execute(
        f"""
        SELECT
            SUM(CASE WHEN event_type='join' THEN 1 ELSE 0 END) AS total_joins,
            SUM(CASE WHEN event_type='leave' THEN 1 ELSE 0 END) AS total_leaves,
            MIN(created_at) AS first_event,
            MAX(created_at) AS last_event
        FROM events
        WHERE {where}
        """,
        params,
    ).fetchone() or {})

    timeseries = [dict(r) for r in conn.execute(
        f"""
        SELECT date(created_at) AS day,
               SUM(CASE WHEN event_type='join' THEN 1 ELSE 0 END) AS joins,
               SUM(CASE WHEN event_type='leave' THEN 1 ELSE 0 END) AS leaves
        FROM events
        WHERE {where}
        GROUP BY day
        ORDER BY day ASC
        """,
        params,
    ).fetchall()]
    hourly = [dict(r) for r in conn.execute(
        f"""
        SELECT strftime('%H', created_at) AS hour, COUNT(*) AS total
        FROM events
        WHERE {where} AND event_type='join'
        GROUP BY hour
        ORDER BY hour
        """,
        params,
    ).fetchall()]
    weekday = [dict(r) for r in conn.execute(
        f"""
        SELECT strftime('%w', created_at) AS weekday, COUNT(*) AS total
        FROM events
        WHERE {where} AND event_type='join'
        GROUP BY weekday
        ORDER BY weekday
        """,
        params,
    ).fetchall()]
    recent_events = [dict(r) for r in conn.execute(
        f"""
        SELECT user_id, username, event_type, created_at
        FROM events
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT 15
        """,
        params,
    ).fetchall()]
    top_members = [dict(r) for r in conn.execute(
        f"""
        SELECT username,
               SUM(CASE WHEN event_type='join' THEN 1 ELSE 0 END) AS joins,
               SUM(CASE WHEN event_type='leave' THEN 1 ELSE 0 END) AS leaves,
               COUNT(*) AS total_events
        FROM events
        WHERE {where}
        GROUP BY username
        ORDER BY total_events DESC, joins DESC, username ASC
        LIMIT 12
        """,
        params,
    ).fetchall()]
    conn.close()

    total_joins = summary.get("total_joins", 0) or 0
    total_leaves = summary.get("total_leaves", 0) or 0
    monthly = _normalize_monthly(an.monthly_stats(timeseries)[-8:])
    return {
        "summary": summary,
        "weekly": an.weekly_stats(timeseries)[-10:],
        "monthly": monthly,
        "insights": an.generate_insights(timeseries, hourly, weekday, summary),
        "top_members": top_members,
        "recent_events": recent_events,
        "peak_hour": an.peak_hour(hourly),
        "peak_day": an.peak_weekday(weekday),
        "total_joins": total_joins,
        "total_leaves": total_leaves,
        "net_growth": total_joins - total_leaves,
        "churn_rate": an.churn_rate(total_joins, total_leaves),
        "event_comparison": _event_comparison(monthly),
    }


def _finance_payload_filtered(chat_id, options=None):
    options = _normalize_export_options(options)
    conn = db.get_connection()
    ref_column = "COALESCE(completed_at, updated_at, created_at)"
    clauses = ["chat_id=?"]
    params = [chat_id]
    extra_clauses, extra_params = _build_date_filters(ref_column, options["start_date"], options["end_date"])
    clauses.extend(extra_clauses)
    params.extend(extra_params)
    where = " AND ".join(clauses)
    paid_statuses = sorted(PAID_STATUSES)
    paid_placeholders = ",".join("?" for _ in paid_statuses)

    metrics = dict(conn.execute(
        f"""
        SELECT
            COUNT(*) AS total_transactions,
            SUM(CASE WHEN lower(status) IN ({paid_placeholders}) THEN amount ELSE 0 END) AS total_revenue,
            SUM(CASE WHEN lower(status) IN ('pending','created','processing','waiting_payment','waiting','open') THEN amount ELSE 0 END) AS pending_amount,
            SUM(CASE WHEN lower(status) IN ({paid_placeholders}) THEN 1 ELSE 0 END) AS approved_total,
            SUM(CASE WHEN lower(status) IN ('pending','created','processing','waiting_payment','waiting','open') THEN 1 ELSE 0 END) AS pending_total
        FROM finance_transactions
        WHERE {where}
        """,
        paid_statuses + paid_statuses + params,
    ).fetchone() or {})

    recent = []
    for tx in conn.execute(
        f"""
        SELECT payment_id, customer_name, provider_account, provider, amount, status,
               COALESCE(completed_at, updated_at, created_at) AS updated_at,
               created_at
        FROM finance_transactions
        WHERE {where}
        ORDER BY COALESCE(completed_at, updated_at, created_at) DESC
        LIMIT 15
        """,
        params,
    ).fetchall():
        tx = dict(tx)
        recent.append({
            "payment_id": tx.get("payment_id") or "-",
            "customer_name": tx.get("customer_name") or "Nao informado",
            "provider_account": tx.get("provider_account") or tx.get("provider") or "-",
            "amount": _to_float(tx.get("amount")),
            "status": str(tx.get("status") or "-"),
            "updated_at": tx.get("updated_at") or tx.get("created_at") or "-",
        })

    monthly = []
    for row in conn.execute(
        f"""
        SELECT
            strftime('%Y-%m', {ref_column}) AS month_key,
            COUNT(*) AS transactions,
            SUM(CASE WHEN lower(status) IN ({paid_placeholders}) THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN lower(status) IN ({paid_placeholders}) THEN amount ELSE 0 END) AS revenue
        FROM finance_transactions
        WHERE {where}
        GROUP BY month_key
        ORDER BY month_key ASC
        """,
        paid_statuses + paid_statuses + params,
    ).fetchall():
        row = dict(row)
        month_key = row.get("month_key") or "-"
        monthly.append({
            "label": _month_label(month_key),
            "transactions": _to_int(row.get("transactions")),
            "approved": _to_int(row.get("approved")),
            "revenue": _to_float(row.get("revenue")),
        })
    conn.close()

    monthly = monthly[-8:]
    current = monthly[-1] if monthly else {"label": "-", "transactions": 0, "approved": 0, "revenue": 0.0}
    previous = monthly[-2] if len(monthly) > 1 else {"label": "-", "transactions": 0, "approved": 0, "revenue": 0.0}
    return {
        "metrics": metrics,
        "recent": recent,
        "monthly": monthly,
        "comparison": {
            "current": current,
            "previous": previous,
            "transactions_delta": current["transactions"] - previous["transactions"],
            "approved_delta": current["approved"] - previous["approved"],
            "revenue_delta": current["revenue"] - previous["revenue"],
        },
    }


def _members_payload_filtered(chat_id):
    members = db.get_members(chat_id)
    count = db.get_member_count(chat_id)
    regulars_total = len([m for m in members if not int(m.get("is_admin") or 0)])
    return {
        "count": count,
        "recent_snapshot": members[:30],
        "regulars_total": regulars_total,
    }


def _campaign_payload_filtered(chat_id):
    sources = db.get_campaign_report(chat_id)
    assignments = db.get_campaign_assignments(chat_id)
    return {
        "total_sources": len(sources),
        "total_assignments": len(assignments),
        "sources": sources[:12],
        "assignments": assignments[:15],
    }


def _report_payload_filtered(chat_id, options=None):
    options = _normalize_export_options(options)
    events = _event_payload_filtered(chat_id, options)
    members = _members_payload_filtered(chat_id)
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "generated_at_file": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "group_title": _group_title(chat_id),
        "filters": options,
        "weekly": events["weekly"],
        "monthly": events["monthly"],
        "insights": events["insights"],
        "top_members": events["top_members"],
        "recent_events": events["recent_events"],
        "peak_hour": events["peak_hour"],
        "peak_day": events["peak_day"],
        "members": members["count"],
        "members_snapshot": members,
        "total_joins": events["total_joins"],
        "total_leaves": events["total_leaves"],
        "net_growth": events["net_growth"],
        "churn_rate": events["churn_rate"],
        "event_comparison": events["event_comparison"],
        "finance": _finance_payload_filtered(chat_id, options),
        "campaigns": _campaign_payload_filtered(chat_id),
        "pixel": _pixel_payload(),
    }


def build_csv_export(chat_id, options=None):
    payload = _report_payload_filtered(chat_id, options)
    sections = payload["filters"]["sections"]
    event_compare = payload["event_comparison"]
    finance = payload["finance"]
    campaigns = payload["campaigns"]
    member_snapshot = payload["members_snapshot"]
    pixel = payload["pixel"]
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Painel HOT", payload["group_title"]])
    writer.writerow(["Gerado em", payload["generated_at_file"]])
    writer.writerow(["Periodo", payload["filters"]["range_label"]])
    writer.writerow(["Escopo", ", ".join([key for key, enabled in sections.items() if enabled]) or "overview"])
    writer.writerow([])

    if sections.get("overview"):
        writer.writerow(["Resumo executivo"])
        writer.writerow(["Indicador", "Valor"])
        writer.writerow(["Entradas totais", payload["total_joins"]])
        writer.writerow(["Saidas totais", payload["total_leaves"]])
        writer.writerow(["Crescimento liquido", payload["net_growth"]])
        writer.writerow(["Churn", _percent(payload["churn_rate"])])
        writer.writerow(["Membros na base", _to_int(payload["members"].get("total"))])
        writer.writerow(["Admins", _to_int(payload["members"].get("admins"))])
        writer.writerow(["Pico de hora", f"{payload['peak_hour'].get('hour', '-')}h"])
        writer.writerow(["Melhor dia", payload["peak_day"].get("weekday", "-")])
        writer.writerow([])

    if sections.get("charts"):
        writer.writerow(["Comparacao com o ultimo mes"])
        writer.writerow(["Metrica", event_compare["previous"]["label"], event_compare["current"]["label"], "Delta", "Tendencia"])
        writer.writerow(["Entradas", event_compare["previous"]["joins"], event_compare["current"]["joins"], event_compare["joins_delta"], _trend(event_compare["current"]["joins"], event_compare["previous"]["joins"])])
        writer.writerow(["Saidas", event_compare["previous"]["leaves"], event_compare["current"]["leaves"], event_compare["leaves_delta"], _trend(event_compare["current"]["leaves"], event_compare["previous"]["leaves"])])
        writer.writerow(["Liquido", event_compare["previous"]["net"], event_compare["current"]["net"], event_compare["net_delta"], _trend(event_compare["current"]["net"], event_compare["previous"]["net"])])
        writer.writerow([])
        writer.writerow(["Evolucao semanal"])
        writer.writerow(["Semana", "Entradas", "Saidas", "Liquido"])
        for row in payload["weekly"]:
            writer.writerow([row["week"], row["joins"], row["leaves"], row["net"]])
        writer.writerow([])
        writer.writerow(["Evolucao mensal"])
        writer.writerow(["Mes", "Entradas", "Saidas", "Liquido"])
        for row in payload["monthly"]:
            writer.writerow([row["label"], row["joins"], row["leaves"], row["net"]])
        writer.writerow([])

    if sections.get("events"):
        writer.writerow(["Eventos recentes"])
        writer.writerow(["Usuario", "Tipo", "Data"])
        for row in payload["recent_events"]:
            writer.writerow([row.get("username") or "-", row.get("event_type") or "-", row.get("created_at") or "-"])
        writer.writerow([])

    if sections.get("members"):
        writer.writerow(["Membros e administradores"])
        writer.writerow(["Indicador", "Valor"])
        writer.writerow(["Membros totais", _to_int(member_snapshot["count"].get("total"))])
        writer.writerow(["Administradores", _to_int(member_snapshot["count"].get("admins"))])
        writer.writerow(["Membros comuns", _to_int(member_snapshot["regulars_total"])])
        writer.writerow([])
        writer.writerow(["Snapshot da base"])
        writer.writerow(["Username", "Nome", "Admin", "Ultimo acesso"])
        for row in member_snapshot["recent_snapshot"]:
            writer.writerow([row.get("username") or "-", row.get("full_name") or "-", "Sim" if row.get("is_admin") else "Nao", row.get("last_seen") or "-"])
        writer.writerow([])

    if sections.get("members") or sections.get("overview"):
        writer.writerow(["Top membros por atividade"])
        writer.writerow(["Username", "Entradas", "Saidas", "Eventos"])
        for row in payload["top_members"]:
            writer.writerow([row.get("username") or "-", row.get("joins") or 0, row.get("leaves") or 0, row.get("total_events") or 0])
        writer.writerow([])

    if sections.get("finance"):
        writer.writerow(["Financeiro PIXGO"])
        writer.writerow(["Indicador", "Valor"])
        writer.writerow(["Faturamento total", _currency(finance["metrics"].get("total_revenue"))])
        writer.writerow(["Pagamentos aprovados", finance["metrics"].get("approved_total") or 0])
        writer.writerow(["Pagamentos pendentes", finance["metrics"].get("pending_total") or 0])
        writer.writerow(["Em aberto", _currency(finance["metrics"].get("pending_amount"))])
        writer.writerow(["Total de transacoes", finance["metrics"].get("total_transactions") or 0])
        writer.writerow([])
        writer.writerow(["Comparacao financeira mensal"])
        writer.writerow(["Metrica", finance["comparison"]["previous"]["label"], finance["comparison"]["current"]["label"], "Delta", "Tendencia"])
        writer.writerow(["Receita", _currency(finance["comparison"]["previous"]["revenue"]), _currency(finance["comparison"]["current"]["revenue"]), _currency(finance["comparison"]["revenue_delta"]), _trend(finance["comparison"]["current"]["revenue"], finance["comparison"]["previous"]["revenue"])])
        writer.writerow(["Aprovadas", finance["comparison"]["previous"]["approved"], finance["comparison"]["current"]["approved"], finance["comparison"]["approved_delta"], _trend(finance["comparison"]["current"]["approved"], finance["comparison"]["previous"]["approved"])])
        writer.writerow(["Transacoes", finance["comparison"]["previous"]["transactions"], finance["comparison"]["current"]["transactions"], finance["comparison"]["transactions_delta"], _trend(finance["comparison"]["current"]["transactions"], finance["comparison"]["previous"]["transactions"])])
        writer.writerow([])
        writer.writerow(["Financeiro por mes"])
        writer.writerow(["Mes", "Transacoes", "Aprovadas", "Receita"])
        for row in finance["monthly"]:
            writer.writerow([row["label"], row["transactions"], row["approved"], _currency(row["revenue"])])
        writer.writerow([])
        writer.writerow(["Ultimas transacoes"])
        writer.writerow(["Pagamento", "Cliente", "Conta", "Valor", "Status", "Atualizado"])
        for row in finance["recent"]:
            writer.writerow([row["payment_id"], row["customer_name"], row["provider_account"], _currency(row["amount"]), row["status"], row["updated_at"]])
        writer.writerow([])

    if sections.get("campaigns"):
        writer.writerow(["Campanhas e atribuicoes"])
        writer.writerow(["Indicador", "Valor"])
        writer.writerow(["Fontes cadastradas", campaigns["total_sources"]])
        writer.writerow(["Membros atribuidos", campaigns["total_assignments"]])
        writer.writerow([])
        writer.writerow(["Resumo por origem"])
        writer.writerow(["Origem", "Tipo", "Entradas", "Saidas", "Membros marcados", "Custo", "Custo por membro"])
        for row in campaigns["sources"]:
            writer.writerow([row.get("name") or "-", row.get("source_type") or "-", row.get("joined_members") or 0, row.get("left_members") or 0, row.get("assigned_members") or 0, _currency(row.get("cost_amount")), _currency(row.get("cost_per_member"))])
        writer.writerow([])

    if sections.get("pixel"):
        writer.writerow(["Tela PIXEL / Meta"])
        writer.writerow(["Campo", "Valor"])
        writer.writerow(["Status", "Conectado" if pixel["ready"] else "Aguardando configuracao"])
        writer.writerow(["Pixel ID", pixel["pixel_id"] or "Nao informado"])
        writer.writerow(["Ad Account ID", pixel["ad_account_id"] or "Nao informado"])
        writer.writerow(["Dataset ID", pixel["dataset_id"] or "Nao informado"])
        writer.writerow(["Test Event Code", pixel["test_event_code"] or "Nao informado"])
        writer.writerow(["Token", pixel["token_preview"] or "Nao configurado"])
        writer.writerow(["Campanhas rodando", pixel["campaigns_running"]])
        writer.writerow(["Campanhas pausadas", pixel["campaigns_paused"]])
        writer.writerow(["Cliques hoje", pixel["clicks_today"]])
        writer.writerow(["Leads hoje", pixel["leads_today"]])
        writer.writerow(["Proximo passo", pixel["next_step"]])
        writer.writerow([])

    if sections.get("overview") or sections.get("charts"):
        writer.writerow(["Insights"])
        writer.writerow(["Resumo"])
        for insight in payload["insights"]:
            writer.writerow([insight])

    return _filename(chat_id, "csv"), ("\ufeff" + buf.getvalue()).encode("utf-8")


def build_pdf_export(chat_id, options=None):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.graphics.shapes import Drawing, Line, Rect, String
    except ImportError as exc:
        raise RuntimeError("reportlab not installed") from exc

    def metric_row(items, widths):
        table = Table([items], colWidths=widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#1e3a8a")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#1e293b")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        return table

    def chart(title, rows, keys, colors_hex):
        drawing = Drawing(520, 210)
        drawing.add(String(0, 192, title, fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
        if not rows:
            drawing.add(String(0, 120, "Sem dados suficientes para o grafico.", fontSize=10, fillColor=colors.HexColor("#64748b")))
            return drawing
        left, bottom, width, height = 38, 34, 450, 120
        drawing.add(Rect(left, bottom, width, height, strokeColor=colors.HexColor("#cbd5e1"), fillColor=None))
        values = []
        for row in rows:
            for key in keys:
                values.append(_to_float(row.get(key)))
        peak = max(values) if values else 1
        if peak <= 0:
            peak = 1
        step = width / max(len(rows) - 1, 1)
        for idx, row in enumerate(rows):
            x = left + (idx * step)
            drawing.add(String(x - 10, bottom - 14, str(row.get("label") or row.get("week") or "")[:8], fontSize=8, fillColor=colors.HexColor("#64748b")))
        for idx, key in enumerate(keys):
            previous = None
            color = colors.HexColor(colors_hex[idx % len(colors_hex)])
            for pos, row in enumerate(rows):
                value = _to_float(row.get(key))
                x = left + (pos * step)
                y = bottom + (value / peak) * height
                drawing.add(Rect(x - 2, y - 2, 4, 4, strokeColor=color, fillColor=color))
                if previous:
                    drawing.add(Line(previous[0], previous[1], x, y, strokeColor=color, strokeWidth=2))
                previous = (x, y)
        return drawing

    payload = _report_payload_filtered(chat_id, options)
    sections = payload["filters"]["sections"]
    finance = payload["finance"]
    campaigns = payload["campaigns"]
    members_snapshot = payload["members_snapshot"]
    pixel = payload["pixel"]
    compare = payload["event_comparison"]
    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=26, rightMargin=26, topMargin=28, bottomMargin=22)
    story = []

    def add_table(title, headers, rows, widths, header_color):
        story.append(Paragraph(title, styles["Heading2"]))
        table = Table([headers] + rows, colWidths=widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d5dbe5")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(table)
        story.append(Spacer(1, 14))

    story.append(Paragraph(f"Painel HOT - {payload['group_title']}", styles["Title"]))
    story.append(Paragraph(f"Relatorio executivo gerado em {payload['generated_at']}", styles["Normal"]))
    story.append(Paragraph(f"Periodo: {payload['filters']['range_label']}", styles["BodyText"]))
    story.append(Paragraph(f"Escopo: {', '.join([key for key, enabled in sections.items() if enabled]) or 'overview'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    if sections.get("overview"):
        cards = []
        for label, value in [("Entradas", str(payload["total_joins"])), ("Saidas", str(payload["total_leaves"])), ("Liquido", str(payload["net_growth"])), ("Churn", _percent(payload["churn_rate"]))]:
            cards.append(Paragraph(f"<font color='#93c5fd' size='9'><b>{label}</b></font><br/><font color='white' size='18'><b>{value}</b></font>", styles["BodyText"]))
        story.append(metric_row(cards, [120, 120, 120, 120]))
        story.append(Spacer(1, 16))
        add_table("Resumo operacional", ["Indicador", "Valor"], [
            ["Membros na base", _to_int(payload["members"].get("total"))],
            ["Admins", _to_int(payload["members"].get("admins"))],
            ["Pico de hora", f"{payload['peak_hour'].get('hour', '-')}h"],
            ["Melhor dia", payload["peak_day"].get("weekday", "-")],
        ], [210, 270], colors.HexColor("#0f172a"))

    if sections.get("charts"):
        add_table("Comparacao com o ultimo mes", ["Metrica", compare["previous"]["label"], compare["current"]["label"], "Delta", "Tendencia"], [
            ["Entradas", compare["previous"]["joins"], compare["current"]["joins"], compare["joins_delta"], _trend(compare["current"]["joins"], compare["previous"]["joins"])],
            ["Saidas", compare["previous"]["leaves"], compare["current"]["leaves"], compare["leaves_delta"], _trend(compare["current"]["leaves"], compare["previous"]["leaves"])],
            ["Liquido", compare["previous"]["net"], compare["current"]["net"], compare["net_delta"], _trend(compare["current"]["net"], compare["previous"]["net"])],
        ], [120, 95, 95, 80, 90], colors.HexColor("#1d4ed8"))
        story.append(chart("Evolucao mensal do grupo", payload["monthly"], ["joins", "leaves", "net"], ["#2563eb", "#ef4444", "#0f766e"]))
        story.append(Spacer(1, 14))
        story.append(chart("Ritmo semanal", payload["weekly"], ["joins", "leaves"], ["#7c3aed", "#f97316"]))
        story.append(Spacer(1, 14))

    if sections.get("events"):
        add_table("Eventos recentes", ["Usuario", "Tipo", "Data"], [[row.get("username") or "-", row.get("event_type") or "-", row.get("created_at") or "-"] for row in payload["recent_events"]] or [["-", "-", "-"]], [170, 90, 220], colors.HexColor("#1e40af"))

    if sections.get("members") or sections.get("overview"):
        add_table("Top membros", ["Username", "Entradas", "Saidas", "Eventos"], [[row.get("username") or "-", row.get("joins") or 0, row.get("leaves") or 0, row.get("total_events") or 0] for row in payload["top_members"]] or [["-", 0, 0, 0]], [210, 85, 85, 85], colors.HexColor("#0f766e"))

    if sections.get("members"):
        add_table("Snapshot da base", ["Username", "Nome", "Admin", "Ultimo acesso"], [[row.get("username") or "-", row.get("full_name") or "-", "Sim" if row.get("is_admin") else "Nao", row.get("last_seen") or "-"] for row in members_snapshot["recent_snapshot"]] or [["-", "-", "-", "-"]], [110, 170, 55, 145], colors.HexColor("#0f766e"))

    if sections.get("overview") or sections.get("charts"):
        story.append(Paragraph("Insights principais", styles["Heading2"]))
        for insight in payload["insights"]:
            story.append(Paragraph(f"- {insight}", styles["BodyText"]))
            story.append(Spacer(1, 4))

    if sections.get("finance"):
        story.append(PageBreak())
        story.append(Paragraph("Financeiro PIXGO", styles["Title"]))
        story.append(Spacer(1, 10))
        finance_cards = []
        for label, value in [("Faturamento total", _currency(finance["metrics"].get("total_revenue"))), ("Aprovadas", str(finance["metrics"].get("approved_total") or 0)), ("Pendentes", str(finance["metrics"].get("pending_total") or 0)), ("Em aberto", _currency(finance["metrics"].get("pending_amount")))]:
            finance_cards.append(Paragraph(f"<font color='#a7f3d0' size='9'><b>{label}</b></font><br/><font color='white' size='16'><b>{value}</b></font>", styles["BodyText"]))
        story.append(metric_row(finance_cards, [120, 120, 120, 120]))
        story.append(Spacer(1, 16))
        add_table("Comparacao financeira mensal", ["Metrica", finance["comparison"]["previous"]["label"], finance["comparison"]["current"]["label"], "Delta", "Tendencia"], [
            ["Receita", _currency(finance["comparison"]["previous"]["revenue"]), _currency(finance["comparison"]["current"]["revenue"]), _currency(finance["comparison"]["revenue_delta"]), _trend(finance["comparison"]["current"]["revenue"], finance["comparison"]["previous"]["revenue"])],
            ["Aprovadas", finance["comparison"]["previous"]["approved"], finance["comparison"]["current"]["approved"], finance["comparison"]["approved_delta"], _trend(finance["comparison"]["current"]["approved"], finance["comparison"]["previous"]["approved"])],
            ["Transacoes", finance["comparison"]["previous"]["transactions"], finance["comparison"]["current"]["transactions"], finance["comparison"]["transactions_delta"], _trend(finance["comparison"]["current"]["transactions"], finance["comparison"]["previous"]["transactions"])],
        ], [120, 110, 110, 90, 80], colors.HexColor("#0f766e"))
        story.append(chart("Receita e aprovacoes por mes", finance["monthly"], ["revenue", "approved"], ["#16a34a", "#0ea5e9"]))
        story.append(Spacer(1, 14))
        add_table("Ultimas transacoes", ["Pagamento", "Cliente", "Conta", "Valor", "Status"], [[row["payment_id"][:28], row["customer_name"], row["provider_account"], _currency(row["amount"]), row["status"]] for row in finance["recent"]] or [["-", "-", "-", _currency(0), "-"]], [150, 125, 90, 70, 85], colors.HexColor("#1f2937"))

    if sections.get("campaigns"):
        story.append(PageBreak())
        story.append(Paragraph("Campanhas e atribuicoes", styles["Title"]))
        story.append(Spacer(1, 10))
        add_table("Resumo por origem", ["Origem", "Tipo", "Entradas", "Saidas", "Marcados", "Custo", "Custo/membro"], [[row.get("name") or "-", row.get("source_type") or "-", row.get("joined_members") or 0, row.get("left_members") or 0, row.get("assigned_members") or 0, _currency(row.get("cost_amount")), _currency(row.get("cost_per_member"))] for row in campaigns["sources"]] or [["-", "-", 0, 0, 0, _currency(0), _currency(0)]], [120, 70, 55, 55, 60, 65, 75], colors.HexColor("#6d28d9"))

    if sections.get("pixel"):
        story.append(PageBreak())
        story.append(Paragraph("Tela PIXEL / Meta", styles["Title"]))
        story.append(Spacer(1, 10))
        pixel_cards = []
        for label, value in [("Status", "Conectado" if pixel["ready"] else "Aguardando"), ("Campanhas rodando", str(pixel["campaigns_running"])), ("Cliques hoje", str(pixel["clicks_today"])), ("Leads hoje", str(pixel["leads_today"]))]:
            pixel_cards.append(Paragraph(f"<font color='#fbcfe8' size='9'><b>{label}</b></font><br/><font color='white' size='16'><b>{value}</b></font>", styles["BodyText"]))
        story.append(metric_row(pixel_cards, [120, 120, 120, 120]))
        story.append(Spacer(1, 16))
        add_table("Status da integracao Meta", ["Campo", "Valor"], [
            ["Pixel ID", pixel["pixel_id"] or "Nao informado"],
            ["Ad Account ID", pixel["ad_account_id"] or "Nao informado"],
            ["Dataset ID", pixel["dataset_id"] or "Nao informado"],
            ["Test Event Code", pixel["test_event_code"] or "Nao informado"],
            ["Token", pixel["token_preview"] or "Nao configurado"],
            ["Proximo passo", pixel["next_step"]],
        ], [170, 310], colors.HexColor("#7c3aed"))

    doc.build(story)
    buf.seek(0)
    return _filename(chat_id, "pdf"), buf.getvalue()
