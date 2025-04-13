import requests
from flask import Flask, render_template, request, jsonify
import sqlite3
import discord
import asyncio
import threading
import os
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

def init_db():
    with sqlite3.connect("apy_alerts.db") as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT,
                pool TEXT,
                chain TEXT,
                project TEXT,
                symbol TEXT,
                condition TEXT,
                threshold REAL,
                notified INTEGER DEFAULT 0
            );
        ''')

init_db()

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"\u2705 Logged in as {client.user}")
    client.loop.create_task(checkalerts_async())


def get_pool_data():
    try:
        res = requests.get("https://yields.llama.fi/pools")
        if res.status_code == 200:
            return res.json().get("data", [])
    except:
        return []
    return []

def load_alerts():
    with sqlite3.connect("apy_alerts.db") as conn:
        cursor = conn.cursor()
        alerts = cursor.execute("SELECT * from alerts WHERE notified = 0").fetchall()
        return alerts


async def checkalerts_async():
    await asyncio.sleep(5)
    while True:
        alerts = load_alerts()
        pools = get_pool_data()

        for alert in alerts:
            alert_id, contact, pool_id, chain, project, symbol, condition, threshold, notified = alert
            try:
                threshold = float(threshold)
            except ValueError:
                continue

            for pool in pools:
                if pool["pool"] == pool_id:
                    current_apy = pool.get("apy", 0)
                    if (condition == "above" and current_apy > threshold) or \
                       (condition == "below" and current_apy < threshold):
                        print(f"\u2705 Alert for {symbol} @ {current_apy}")
                        await send_notif(contact, project, symbol, current_apy, condition, threshold)

                        with sqlite3.connect("apy_alerts.db") as conn:
                            conn.execute("UPDATE alerts SET notified = 1 where id = ?", (alert_id,))

        await asyncio.sleep(5)


async def send_notif(contact, project, symbol, current_apy, condition, threshold):
    try:
        user = await client.fetch_user(contact)
        msg = f"{project} ({symbol}) APY is {current_apy} which is {condition} your {threshold}"
        await user.send(msg)
        print(f"Sent alert to {user.name}")
    except Exception as e:
        print(f"Error sending DM: {e}")


def run_flask():
    app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        chain = request.form.get("chain").capitalize()
        sort_by = request.form.get("sort_by", "alphabetical")

        data = blocks(chain)

        if sort_by== "apy":
            data.sort(key=lambda p: p.get("apy", 0), reverse=True)
        elif sort_by =="tvl":
            data.sort(key=lambda p: p.get("tvl", 0), reverse=True)
        else:
            data.sort(key=lambda p: p.get("project", "").lower())

        return render_template("index.html", pools = data)

    else:
        return render_template("index.html", pools= [])


@app.route("/calculate", methods=["GET", "POST"])
def calculate():

    response = requests.get("https://yields.llama.fi/pools")

    protocols = []

    if response.status_code == 200:
        data = response.json()
        for pool in data["data"]:
            protocols.append(pool)
        
        protocols.sort(key=lambda p: p.get("project", "").lower())
    else:
        protocols = []

    return render_template("calculate.html", protocols=protocols)


@app.route("/graph/<pool_id>")
def graph(pool_id):

    final = historical_data(pool_id)

    response = requests.get("https://yields.llama.fi/pools")

    if response.status_code == 200:
        data = response.json()
        for pool in data["data"]:
            if pool["pool"] == pool_id:
                current_apy = pool["apy"]

    if final: 
        return render_template("graph.html", pool_id= pool_id, historical_data= final, current_apy = current_apy)
    else:
        return render_template("graph.html", pool_id= pool_id, historical_data= [], current_apy = None)


@app.route("/graph_data/<pool_id>")
def graph_data(pool_id):
    amount = int(request.args.get("amount", 1000))
    years = int(request.args.get("years", 3))

    response = requests.get("https://yields.llama.fi/pools")
    data = response.json()

    apy = 0
    for pool in data["data"]:
        if pool_id == pool["pool"]:
            apy = pool["apy"]
            break

    datapoints = []
    value = amount
    for year in range(1, years+1):
        value = value* (1 + apy / 100)
        datapoints.append({"year": year, "value": round(value,2)})

    return jsonify(datapoints)



@app.route("/returns", methods = ["POST"])
def returns():
    amount = int(request.form.get("amount"))
    pool_id = request.form.get("protocol")
    years = int(request.form.get("duration"))

    response = requests.get("https://yields.llama.fi/pools")

    apy = 0 
    data = response.json()

    for pool in data["data"]:
        if pool_id == pool["pool"]:
            apy = pool["apy"]
            name = pool["project"]
            symbol = pool["symbol"]
            break
    
    protocols = []

    if response.status_code == 200:
        data = response.json()
        for pool in data["data"]:
            protocols.append(pool)
        
        protocols.sort(key=lambda p: p.get("project", "").lower())
    else:
        protocols = []


    datapoints = []
    value = amount
    for year in range(1, years+1):
        value = value* (1 + apy / 100)
        datapoints.append({"year": year, "value": round(value,2)})

    return render_template("returnsgraph.html", amount = amount, apy=apy, name =name, symbol= symbol, datapoints=datapoints, protocols= protocols)
        

@app.route("/alert")
def alert():
    protocols = get_pool_data()
    protocols.sort(key=lambda p: p.get("project", "").lower())
    return render_template("alert.html", protocols=protocols)

@app.route("/setalert", methods=["POST"])
def setalert():
    contact = request.form["contact"]
    pool_id = request.form["protocol"]
    condition = request.form["condition"]
    threshold = request.form["threshold"]

    pools = get_pool_data()
    selected = next((p for p in pools if p["pool"] == pool_id), None)
    if not selected:
        return "❌ Pool not found", 400

    with sqlite3.connect("apy_alerts.db") as db:
        db.execute('''
            INSERT INTO alerts (contact, pool, chain, project, symbol, condition, threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (contact, pool_id, selected["chain"], selected["project"], selected["symbol"], condition, threshold))

    return "✅ Alert saved successfully!"


def blocks(chain):

    pools = []

    response = requests.get("https://yields.llama.fi/pools")

    if response.status_code == 200:
        data = response.json()
        for pool in data["data"]:
            if pool["chain"] == chain:
                pools.append(pool)

        return pools
    else:
        return []
        

def historical_data(pool_id):


    history = []
    historical = f"https://yields.llama.fi/chart/{pool_id}"
    res = requests.get(historical)

    if res.status_code == 200:
        data = res.json()
        for his in data["data"]:
            history.append(his)
        return history
    else:
        return []


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run(TOKEN)
