gl = globals
from flask import *
globals = gl
from base import *
app=Flask("whalerank")
from flaskext.markdown import Markdown
Markdown(app)

@app.route("/")
def view_index():
    readme = open("README.md").read().replace("https://whalerank.py3.io/", "/") #replace to relative link for local dev
    return render_template("index.html", readme=readme)

BANK="0xc18907269640d11e2a91d7204f33c5115ce3419e"
def rabbit_getprice(ibtoken, realtoken):
    totalToken = callfunction(B, BANK, "totalToken(address)", addrtoarg(realtoken)) 
    totalSupply = callfunction(B, ibtoken, "totalSupply()", "")
    return D(totalToken)/D(totalSupply)

def alpaca_getprice(ibtoken):
    totalToken = callfunction(B, ibtoken, "totalToken()", "") 
    totalSupply = callfunction(B, ibtoken, "totalSupply()", "")
    return D(totalToken)/D(totalSupply)


rabbit_ibBUSD = "0xe0d1130def49c29a4793de52eac680880fc7cb70"
BUSD="0xe9e7cea3dedca5984780bafc599bd69add087d56"
rabbit_ibUSDT = "0xfe1622f9f594a113cd3c1a93f7f6b0d3c0588781"
USDT="0x55d398326f99059ff775485246999027b3197955"
alpaca_ibBUSD = "0x7c9e73d4c71dae564d41f78d56439bb4ba87592f"
alpaca_ibUSDT = "0x158da805682bdc8ee32d52833ad41e74bb951e59"

millnames = ['',' Thousand',' Million',' Billion',' Trillion']

def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.1f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

def view_rabbit(ibtoken, realtoken, pid, tablename):
    lastblock = runsql(f"SELECT max(blockid) FROM `{tablename}`")[0][0]
    try:
        block = eth_getBlockByNumber(lastblock)
        ts = int(block["timestamp"], 16)
        timestr = datetime.fromtimestamp(ts).strftime("%Y/%m/%d %H:%M:%S")
        ago = int(time.time()-ts)
        last_update = f"<span title='{timestr}'>{ago}s ago</span> (Block {lastblock})"
    except:
        traceback.print_exc()
        last_update = f"Block {lastblock}"
    try:
        if tablename=="rabbitstaking":
            ib_price = rabbit_getprice(ibtoken, realtoken)
        elif tablename == "alpacastaking":
            ib_price = alpaca_getprice(ibtoken)
    except:
        traceback.print_exc()
        ib_price = 1
    data = runsql(f"SELECT user, sum(amount)/1000000 as a FROM `rabbitstaking` where pid={pid} group by user order by a desc limit 100;")
    t = globals()
    t.update(locals())
    return render_template("rabbit.html", **t)

@app.route("/rabbit/busd")
def view_rabbit_busd():
    return view_rabbit(rabbit_ibBUSD, BUSD, 1, tablename="rabbitstaking")

@app.route("/rabbit/usdt")
def view_rabbit_usdt():
    return view_rabbit(rabbit_ibUSDT, USDT, 2, tablename="rabbitstaking")

@app.route("/alpaca/busd")
def view_alpaca_busd():
    return view_rabbit(alpaca_ibBUSD, BUSD, 3, tablename="alpacastaking")

@app.route("/alpaca/usdt")
def view_alpaca_usdt():
    return view_rabbit(alpaca_ibUSDT, USDT, 16, tablename="alpacastaking")

if __name__ == "__main__":
    app.run(debug=os.environ.get("DEBUG", False), host="0.0.0.0", port=5001)