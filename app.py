gl = globals
from flask import *
globals = gl
from base import *
app=Flask("whalerank")

@app.route("/")
def view_index():
    return redirect("https://github.com/zjuchenyuan/whalerank")

BANK="0xc18907269640d11e2a91d7204f33c5115ce3419e"
def rabbit_getprice(ibtoken, realtoken):
    totalToken = callfunction(B, BANK, "totalToken(address)", addrtoarg(realtoken)) 
    totalSupply = callfunction(B, ibtoken, "totalSupply()", "")
    return D(totalToken)/D(totalSupply)

ibBUSD = "0xe0d1130def49c29a4793de52eac680880fc7cb70"
BUSD="0xe9e7cea3dedca5984780bafc599bd69add087d56"
ibUSDT = "0xfe1622f9f594a113cd3c1a93f7f6b0d3c0588781"
USDT="0x55d398326f99059ff775485246999027b3197955"

import math

millnames = ['',' Thousand',' Million',' Billion',' Trillion']

def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.1f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

def view_rabbit(ibtoken, realtoken, pid):
    lastblock = runsql(f"SELECT max(blockid) FROM `rabbitstaking`")[0][0]
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
        ib_price = rabbit_getprice(ibtoken, realtoken)
    except:
        traceback.print_exc()
        ib_price = 1
    data = runsql(f"SELECT user, sum(amount)/1000000 as a FROM `rabbitstaking` where pid={pid} group by user order by a desc limit 100;")
    t = globals()
    t.update(locals())
    return render_template("rabbit.html", **t)

@app.route("/rabbit/busd")
def view_rabbit_busd():
    return view_rabbit(ibBUSD, BUSD, 1)

@app.route("/rabbit/usdt")
def view_rabbit_usdt():
    return view_rabbit(ibUSDT, USDT, 2)

if __name__ == "__main__":
    app.run(debug=os.environ.get("DEBUG", False), host="0.0.0.0", port=5001)