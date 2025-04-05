import requests
from flask import Flask, render_template, request

app = Flask(__name__)

url = "https://yields.llama.fi/pools"


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
    
    datapoints = []
    value = amount
    for year in range(1, years+1):
        value = value* (1 + apy / 100)
        datapoints.append({"year": year, "value": round(value,2)})

    return render_template("returnsgraph.html", amount = amount, apy=apy, name =name, symbol= symbol, datapoints=datapoints)
        

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

