gl = globals
from flask import *
globals = gl
from base import *
from functools import lru_cache
import eth_abi
app=Flask("whalerank")
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2)
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

def cached_runsql(*args, **kwargs):
    ttl_hash = int(time.time()/300)
    return real_cached_runsql(ttl_hash, *args, **kwargs)[:]

@lru_cache()
def real_cached_runsql(ttl_hash, *args, **kwargs):
    #print("[cache miss]", args[0])
    ts = time.time()
    res = runsql(*args, **kwargs)
    #print("runsql time:", time.time()-ts)
    return res

def table2last_update(tablename, endpoint=None):
    lastblock = cached_runsql(f"SELECT max(blockid) FROM `{tablename}`")[0][0]
    try:
        block = eth_getBlockByNumber(lastblock, endpoint=endpoint)
        ts = int(block["timestamp"], 16)
        timestr = datetime.fromtimestamp(ts).strftime("%Y/%m/%d %H:%M:%S")
        ago = int(time.time()-ts)
        last_update = f"<span title='{timestr}'>{ago}s ago</span> (Block {lastblock})"
    except:
        traceback.print_exc()
        last_update = f"Block {lastblock}"
    return last_update

def view_rabbit(ibtoken, realtoken, pid, tablename):
    last_update = table2last_update(tablename)
    try:
        if tablename=="rabbitstaking":
            ib_price = rabbit_getprice(ibtoken, realtoken)
        elif tablename == "alpacastaking":
            ib_price = alpaca_getprice(ibtoken)
    except:
        traceback.print_exc()
        ib_price = 1
    data = cached_runsql(f"SELECT user, sum(amount)/1000000 as a FROM `{tablename}` where pid={pid} group by user order by a desc limit 100;")
    addrs = [i[0] for i in data]
    nonces = batch_getTransactionCount(addrs)
    for idx,i in enumerate(data):
        data[idx] = [*i, nonces[idx]]
    t = globals()
    t.update(locals())
    return render_template("rabbit.html", **t)

def pendingkey(addresses, endpoint=B):
    farm="0x529E2a515CE4499C41B23102E56e45025e393757"
    x = batch_callfunction_decode(endpoint, [ 
        [farm,"getUserFarmInfos(uint256[],address)",b16encode(eth_abi.encode_abi(["uint256[]","address"], [list(range(0,22)),addr])).decode().lower()] 
            for addr in addresses], 
        ['(uint256[],uint256[],uint256[],uint256[],uint256)']
    )
    return [Decimal(sum(i[3]))/10**18 for i in x]

def view_momo(pid, tablename="momo", tokenprice=1, endpoint=B, template="momo.html"):
    last_update = table2last_update(tablename, endpoint=endpoint)
    ts = time.time()
    data = cached_runsql(f"SELECT user, sum(amount)/1000000 as a FROM `{tablename}` where pid={pid} group by user order by a desc limit 100;")
    addrs = [i[0] for i in data]
    nonces = batch_getTransactionCount(addrs, endpoint=endpoint)
    if template=="momo.html":
        keys = pendingkey(addrs, endpoint=endpoint)
        sum_key = "%.1f"%sum(keys)
    for idx,i in enumerate(data):
        data[idx] = [i[0], i[1]*tokenprice, nonces[idx]]
        if template=="momo.html":
            data[idx].append("%.1f"%keys[idx])
    t = globals()
    t.update(locals())
    return render_template(template, **t)

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

mobox_pools={
 1: ('BTCB-WBNB', '0x7561eee90e24f3b348e1087a005f78b4c8453524'),
 2: ('ETH-WBNB', '0x70d8929d04b60af4fb9b58713ebcf18765ade422'),
 3: ('WBNB-BUSD', '0x1b96b92314c44b159149f7e0303511fb2fc4774f'),
 4: ('USDT-WBNB', '0x20bcc3b8a0091ddac2d0bc30f68e6cbb97de59cd'),
 5: ('USDT-BUSD', '0xc15fa3e22c912a276550f3e5fe3b0deb87b55acd'),
 6: ('DAI-BUSD', '0x3ab77e40340ab084c3e23be8e5a6f7afed9d41dc'),
 7: ('USDC-BUSD', '0x680dd100e4b394bda26a59dd5c119a391e747d18'),
 8: ('BUSD', '0xe9e7cea3dedca5984780bafc599bd69add087d56'),
 9: ('USDT', '0x55d398326f99059ff775485246999027b3197955'),
 10: ('USDC', '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'),
 12: ('MBOX-WBNB', '0x8d42ee6f423a5016792e6d0d4508c05f30cac5bc'),
 14: ('BTCB-WBNB', '0x61eb789d75a95caa3ff50ed7e47b96c132fec082'),
 15: ('ETH-WBNB', '0x74e4716e431f45807dcf19f284c7aa99f18a4fbc'),
 16: ('WBNB-BUSD', '0x58f876857a02d6762e0101bb5c46a8c1ed44dc16'),
 17: ('USDT-WBNB', '0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae'),
 18: ('USDT-BUSD', '0x7efaef62fddcca950418312c6c91aef321375a00'),
 19: ('DAI-BUSD', '0x66fdb2eccfb58cf098eaa419e5efde841368e489'),
 20: ('USDC-BUSD', '0x2354ef4df11afacb85a5c7f98b624072eccddbb1'),
 21: ('MBOX-WBNB', '0x8fa59693458289914db0097f5f366d771b7a7c3f')
}

@app.route("/mobox/busd")
def view_mobox_busd():
    return view_momo(8)

@app.route("/mobox/usdt")
def view_mobox_usdt():
    return view_momo(9)

@app.route("/mobox/usdc")
def view_mobox_usdc():
    return view_momo(10)

@app.route("/mobox/usdt-busd")
def view_mobox_usdtbusd(id=18):
    lpprice = lppool_value(B, mobox_pools[id][1], 10**18, token1_nodecimal_price=D(1)/10**18)
    print("lpprice:", lpprice)
    return view_momo(id, tokenprice=lpprice)

@app.route("/mobox/dai-busd")
def view_mobox_daibusd():
    return view_mobox_usdtbusd(id=19)

@app.route("/mobox/usdc-busd")
def view_mobox_usdcbusd():
    return view_mobox_usdtbusd(id=20)

@app.route("/mobox/usdt-busd_old")
def view_mobox_usdtbusd_old():
    return view_mobox_usdtbusd(id=5)

M = "https://matic.mytokenpocket.vip/"

@app.route("/maticiron/3usd")
def view_maticiron_3usd():
    token_price = D(callfunction(M, "0x837503e8a8753ae17fb8c8151b8e6f586defcb57", "calculateRemoveLiquidityOneToken(address,uint256,uint8)", addrtoarg("0x0000000000000000000000000000000000000000")+hex(10**(18+3))[2:].rjust(64,"0")+"0"*64,))/10**(6+3)
    return view_momo(0, tablename="maticiron", tokenprice=token_price, endpoint=M, template="maticiron.html")

if __name__ == "__main__":
    app.run(debug=os.environ.get("DEBUG", False), host="127.0.0.1", port=5001, threaded=True, use_reloader=False)