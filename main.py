import os, re, asyncio, json
from datetime import datetime
from threading import Thread
from flask import Flask, jsonify, render_template_string
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
WATCH = ["HBL","UBL","OGDC","PPL","LUCK","ENGRO","MCB","FFC"]
data = {s: {"ltp": None, "chg": None, "pct": None, "time": None} for s in WATCH}

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def parse(msg):
    out = {}
    for sym in WATCH:
        m = re.search(rf"\b{sym}\b[^0-9]*([0-9]+\.?[0-9]*)\s*([+-][0-9]+\.?[0-9]*)?\s*\(?([+-]?[0-9]+\.?[0-9]*)%?\)?", msg, re.I)
        if m:
            ltp = float(m.group(1))
            chg = float(m.group(2)) if m.group(2) else None
            pct = float(m.group(3)) if m.group(3) else None
            out[sym] = (ltp, chg, pct)
    return out

@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")

@bot.event
async def on_message(m):
    if m.author.bot: return
    upd = parse(m.content)
    now = datetime.now().strftime("%H:%M:%S")
    for s,(ltp,chg,pct) in upd.items():
        data[s] = {"ltp":ltp, "chg":chg, "pct":pct, "time":now}

app = Flask(__name__)

HTML = """<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1">
<title>PSX Live</title><style>
body{font-family:system-ui;background:#0b0f14;color:#e6e6e6;margin:0;padding:16px}
h1{font-size:20px;margin:0 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.card{background:#121821;border:1px solid #1f2937;border-radius:14px;padding:12px}
.sym{font-weight:700;font-size:16px}
.ltp{font-size:22px;margin:6px 0}
.chg{font-size:14px}
.up{color:#22c55e}.dn{color:#ef4444}.zz{color:#9ca3af}
.time{font-size:11px;color:#6b7280;margin-top:6px}
</style></head><body>
<h1>PSX Live – Watchlist</h1>
<div class=grid id=g></div>
<script>
async function load(){
  const r=await fetch('/data'); const d=await r.json();
  const g=document.getElementById('g'); g.innerHTML='';
  Object.entries(d).forEach(([s,v])=>{
    const chg=v.chg??0; const cls=chg>0?'up':chg<0?'dn':'zz';
    const pct=v.pct!=null?`(${v.pct>0?'+':''}${v.pct}%)`:'';
    g.innerHTML+=`<div class=card><div class=sym>${s}</div>
      <div class=ltp>${v.ltp??'—'}</div>
      <div class="chg ${cls}">${v.chg!=null?(v.chg>0?'+':'')+v.chg:''} ${pct}</div>
      <div class=time>${v.time??''}</div></div>`;
  });
}
load(); setInterval(load,5000);
</script></body></html>"""

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/data")
def get_data(): return jsonify(data)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

Thread(target=run_flask, daemon=True).start()
asyncio.run(bot.start(TOKEN)) if TOKEN else print("Set DISCORD_TOKEN")
