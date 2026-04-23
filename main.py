import os, time, threading, requests
from flask import Flask, jsonify, render_template_string

# PSX symbols for psxterminal.com API
WATCHLIST = ["HBL","UBL","OGDC","PPL","LUCK","ENGRO","MCB","FFC"]

DATA = {sym: {"price": None, "change": None, "pct": None, "time": None} for sym in WATCHLIST}

app = Flask(__name__)

HTML = """
<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PSX Live – Real PSX</title>
<style>
body{background:#0b0d12;color:#e8ecf1;font-family:system-ui;margin:0;padding:16px}
h1{font-size:20px;margin:0 0 12px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.card{background:#141821;border:1px solid #222938;border-radius:16px;padding:14px}
.sym{opacity:.8;font-size:13px}
.price{font-size:28px;margin:6px 0}
.chg{font-size:14px}
.up{color:#22c55e}.down{color:#ef4444}.flat{color:#9aa4b2}
.time{opacity:.6;font-size:11px;margin-top:6px}
.footer{opacity:.5;font-size:11px;margin-top:16px;text-align:center}
</style></head><body>
<h1>PSX Live – Pakistan Stock Exchange</h1>
<div class="grid" id="g"></div>
<div class="footer">Updates every 30s from PSX Terminal • Real data</div>
<script>
async function load(){
  const r=await fetch('/api'); const d=await r.json();
  const g=document.getElementById('g'); g.innerHTML='';
  Object.entries(d).forEach(([s,v])=>{
    const c=v.change??0; const cls=c>0?'up':c<0?'down':'flat';
    const price=v.price!=null?Number(v.price).toLocaleString():'—';
    const chg=v.change!=null?`${v.change>0?'+':''}${v.change} (${v.pct>0?'+':''}${v.pct}%)`:'—';
    g.innerHTML+=`<div class="card"><div class="sym">${s}</div><div class="price">${price}</div><div class="chg ${cls}">${chg}</div><div class="time">${v.time||''}</div></div>`;
  });
}
load(); setInterval(load,15000);
</script></body></html>
"""

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/api")
def api(): return jsonify(DATA)

def fetch_prices():
    while True:
        for sym in WATCHLIST:
            try:
                url = f"https://psxterminal.com/api/ticks/REG/{sym}"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    j = r.json()
                    # psxterminal returns dict with various keys - handle common variants
                    price = j.get("last") or j.get("ltp") or j.get("close") or j.get("price")
                    change = j.get("change") or j.get("netChange")
                    pct = j.get("changePercent") or j.get("percentChange") or j.get("pct_change")
                    
                    # sometimes nested in 'data'
                    if not price and isinstance(j.get("data"), dict):
                        d = j["data"]
                        price = d.get("last") or d.get("ltp")
                        change = d.get("change")
                        pct = d.get("changePercent")
                    
                    if price:
                        DATA[sym] = {
                            "price": round(float(price),2),
                            "change": round(float(change or 0),2),
                            "pct": round(float(pct or 0),2),
                            "time": time.strftime("%H:%M:%S", time.gmtime(time.time()+4*3600))
                        }
            except Exception as e:
                print("Error", sym, e)
        time.sleep(30)

threading.Thread(target=fetch_prices, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
