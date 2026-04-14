from collections import defaultdict
from datetime import datetime

DIAS = ["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"]

def moving_avg(vals, w=7):
    out = []
    for i in range(len(vals)):
        s = max(0, i-w+1)
        out.append(round(sum(vals[s:i+1])/(i-s+1), 2))
    return out

def churn_rate(j, l):
    return round((l/j)*100, 2) if j else 0.0

def net_series(ts):
    net, out = 0, []
    for r in ts:
        net += r["joins"] - r["leaves"]
        out.append(net)
    return out

def detect_spikes(ts, mult=2.0):
    if not ts: return []
    vals = [r["joins"] for r in ts]
    avg  = sum(vals)/len(vals)
    return [{"day":r["day"],"joins":r["joins"],
             "vs_avg": round(r["joins"]/avg,1) if avg else 0}
            for r in ts if r["joins"] > avg*mult and r["joins"] > 5]

def detect_drops(ts, mult=2.0):
    return [{"day":r["day"],"leaves":r["leaves"],"joins":r["joins"]}
            for r in ts if r["leaves"] > r["joins"]*mult and r["leaves"] > 3]

def peak_hour(hourly):
    return max(hourly, key=lambda x: x["total"]) if hourly else {}

def peak_weekday(wd):
    if not wd: return {}
    best = max(wd, key=lambda x: x["total"])
    return {"weekday": DIAS[int(best["weekday"])], "total": best["total"]}

def weekly_stats(ts):
    agg = defaultdict(lambda: {"joins":0,"leaves":0})
    for r in ts:
        try:
            w = datetime.strptime(r["day"],"%Y-%m-%d").strftime("%Y-W%W")
            agg[w]["joins"]  += r["joins"]
            agg[w]["leaves"] += r["leaves"]
        except: pass
    return [{"week":k,**v,"net":v["joins"]-v["leaves"]} for k,v in sorted(agg.items())]

def monthly_stats(ts):
    agg = defaultdict(lambda: {"joins":0,"leaves":0})
    for r in ts:
        try:
            m = r["day"][:7]
            agg[m]["joins"]  += r["joins"]
            agg[m]["leaves"] += r["leaves"]
        except: pass
    return [{"month":k,**v,"net":v["joins"]-v["leaves"]} for k,v in sorted(agg.items())]

def generate_insights(ts, hourly, wd, summary):
    out = []
    for s in detect_spikes(ts)[:3]:
        out.append(f"📈 Pico em {s['day']}: {s['joins']} entradas ({s['vs_avg']}× média)")
    for d in detect_drops(ts)[:2]:
        out.append(f"📉 Alto churn em {d['day']}: {d['leaves']} saídas vs {d['joins']} entradas")
    ph = peak_hour(hourly)
    if ph: out.append(f"⏰ Pico às {ph['hour']}h com {ph['total']} entradas")
    pw = peak_weekday(wd)
    if pw: out.append(f"📅 Dia mais ativo: {pw['weekday']} com {pw['total']} entradas")
    tj = summary.get("total_joins",  0) or 0
    tl = summary.get("total_leaves", 0) or 0
    cr = churn_rate(tj, tl)
    if cr > 50: out.append(f"⚠️ Churn alto: {cr}% — avalie engajamento")
    elif cr < 20 and tj > 0: out.append(f"✅ Churn baixo: {cr}% — retenção saudável!")
    if not out: out.append("ℹ️ Poucos dados ainda. Continue monitorando!")
    return out