import requests
from flask import Flask, render_template, request

app = Flask(__name__)

url = "https://yields.llama.fi/pools"
response = requests.get(url)



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        chain = request.form.get("chain").capitalize()

        data = blocks(chain)

        return render_template("index.html", pools = data)

    else:
        return render_template("index.html", pools= [])
    

@app.route("/graph/<pool_id>")
def graph(pool_id):

    final = historical_data(pool_id)

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
    
    protocols = []

    if response.status_code == 200:
        data = response.json()
        for pool in data["data"]:
            protocols.append(pool)
    else:
        protocols = []

    return render_template("calculate.html", protocols=protocols)

@app.route("/returns", methods = ["POST"])
def returns():
    amount = int(request.form.get("amount"))
    pool_id = request.form.get("protocol")
    years = int(request.form.get("duration"))

    apy = 0 
    data = response.json()

    for pool in data["data"]:
        if pool_id == pool["pool"]:
            apy = pool["apy"]
            break
    
    datapoints = []
    value = amount
    for year in range(1, years+1):
        value = value* (1 + apy / 100)
        datapoints.append({"year": year, "value": round(value,2)})

    return render_template("returnsgraph.html", amount = amount, apy=apy, datapoints=datapoints)
        




def blocks(chain):

    pools = []

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




# print(item["project"], "(", item["symbol"], ")" , " : ", 




# Filter for entries on the Solana chain and with USDC as the token
# if 
# solana_usdc_yields = [
#     item for item in data 
#     if item.get("chain", "").lower() == "solana" and item.get("token", "").upper() == "USDC"
# ]

# print(solana_usdc_yields)

