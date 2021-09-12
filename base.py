import time, requests, hashlib, random, json, os, subprocess, sys, threading, traceback, pickle, math
from datetime import datetime
from decimal import Decimal
from base64 import b16decode, b16encode
from time import sleep
from copy import deepcopy
from collections import Counter
from runsql import *
from config import *
BSC_NODES = ["https://bsc-dataseed.binance.org/", 
"https://bsc-dataseed1.defibit.io/", 
"https://bsc-dataseed3.ninicoin.io/",
"https://bsc-dataseed4.binance.org/", 
"https://bsc-dataseed2.ninicoin.io/",
"https://bsc-dataseed4.defibit.io/",
"https://bsc-dataseed2.binance.org/",]
B=BSC_NODES[0]

sess=requests.session()
toi = lambda x:int(x,16)

from Crypto.Hash import keccak

def event_hash(s):
    return keccak.new(digest_bits=256).update(s.encode("utf-8")).hexdigest()

def function_hash(func_str):
    return event_hash(func_str)[:8]

def addrtoarg(addr):
    if isinstance(addr, int):
        addr = hex(addr)
    if addr.startswith("0x"):
        addr = addr[2:]
    return addr.lower().rjust(64, "0")
toarg = addrtoarg

def callfunction(endpoint, addr, func_str, args_str, blockid="latest", returnint=True):
    if os.environ.get("DEBUG", False):
        print("[callfunction]", addr, func_str, "0x"+function_hash(func_str)+args_str, end="", flush=True)
    try:
        height = hex(int(blockid))
    except:
        height = blockid
    data = {
        "id":1, "jsonrpc":"2.0",
        "method":"eth_call",
        "params":[{"data": "0x"+function_hash(func_str)+args_str, "to": addr,}, height]
    }
    x = sess.post(endpoint, json=data, timeout=5)
    if os.environ.get("DEBUG", False):
        print()
    try:
        res = x.json()["result"]
    except:
        print(x.request.body, x.json())
        raise
    if not returnint:
        return res
    else:
        return int(res, 16)

def batch_callfunction(endpoint, datalist, height):
    data = []
    idx = -1
    if os.environ.get("DEBUG", False):
        print("[batch_call]", len(datalist), "calls")
    for addr, func_str, args_str in datalist:
        idx += 1
        if func_str.startswith("eth_"):
            data.append({"id": idx, "jsonrpc":"2.0", "method":func_str,
                "params": [args_str, height]
            })
        else:
            data.append({"id": idx, "jsonrpc":"2.0", "method":"eth_call",
                "params":[{"data": "0x"+function_hash(func_str)+args_str, "to": addr,}, height]
            })
    if os.environ.get("DEBUG_VERBOSE", False):
        print(data)
    x = sess.post(endpoint, json=data, timeout=10)
    if os.environ.get("DEBUG_VERBOSE", False):
        print(x.json())
    res = [(i["id"],i.get("result", None)) for i in x.json()]
    return res

def bd(result_str):
    # base64 decode rpc result str, return bytes
    if isinstance(result_str, tuple) and len(result_str)==2 and isinstance(result_str[0], int):
        result_str = result_str[1]
    if result_str.startswith("0x"):
        result_str = result_str[2:]
        if len(result_str)%2!=0:
            result_str = "0"+result_str
    return b16decode(result_str.upper())

def batch_callfunction_decode(endpoint, datalist, outtypes, height=None, needidx=False):
    """
    datalist: [contract_address, funcname(arg_type_list), encoded_arguments]
    outtypes: list of [return values' type list]
    Example:
        data = batch_callfunction_decode(H, [[addr, "symbol()", ""] for addr in addrs], [["string"]])
    Depends on eth_abi package
    """
    import eth_abi
    if not height:
        height = "latest"
    if not isinstance(outtypes[0], list):
        outtypes = [outtypes]*len(datalist)
    data = batch_callfunction(endpoint, datalist, height)
    res = []
    for i, item in data:
        if not item:
            res.append((i, None))
        else:
            #print(outtypes[i], item)
            if outtypes[i]==["hex"]:
                d = int(item, 16)
            else:
                d = eth_abi.decode_abi(outtypes[i], bd(item))
                if len(d)==1:
                    d = d[0]
            res.append((i, d))
    if needidx:
        return res
    else:
        return [i[1] for i in res]

def scan_txlist(address, page=1, endpoint="api.bscscan.com", retry=3, toblock=None, APIKEY=BSC_SCANKEY):
    url = f"https://{endpoint}/api?apikey={APIKEY}&module=account&action=txlist&address={address}&sort=desc&page={page}&offset=1000"
    if toblock:
        url += f"&endblock={toblock}"
    x = sess.get(url)
    d = x.json()
    if not isinstance(d["result"], list):
        if retry:
            sleep(2)
            return scan_txlist(address, page=page, endpoint=endpoint, retry=retry-1)
        else:
            raise Exception(x.text)
    return d["result"]

def cached_scan_txlist(address, page, note="bsc", endpoint="api.bscscan.com"):
    cachefile = f"__pycache__/{note}txlist_{address}_{page}"
    if os.path.isfile(cachefile):
        try:
            return json.load(open(cachefile))
        except:
            pass
    res = scan_txlist(address, page=page, endpoint=endpoint)
    open(cachefile,"w").write(json.dumps(res))
    return res

def eth_getBlockByNumber(height, urls=BSC_NODES, retry=3, endpoint=None):
    if endpoint:
        urls = [endpoint]
        url = endpoint
    else:
        url = urls[0]
    if isinstance(height, int):
        height = hex(height)
    res = {}
    try:
        x = sess.post(url, json={"id":random.randint(0,9999),"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":[height,True]}, timeout=5)
        if os.environ.get("DEBUG_VERBOSE", False):
            print(url, x, x.text, height)
        res = x.json()["result"]
    except:
        pass
    if "transactions" not in res:
        if retry:
            sleep(2)
            random.shuffle(urls)
            print("change api to", urls[0])
            return eth_getBlockByNumber(height, urls=urls, retry=retry-1, endpoint=endpoint)
        else:
            raise Exception(x.text)
    return res

def batch_eth_getBlockByNumber(heights, endpoint=None):
    data = []
    for height in heights:
        if isinstance(height, int):
            height = hex(height)
        data.append({"id":len(data),"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":[height,True]})
    def f(res):
        assert res and "transactions" in res[0]["result"]
    res = batch_callRPC(data, checkfunc=f, endpoint=endpoint)
    return [i["result"] for i in res]

def createtable_tx(tablename):
    sql = f"""CREATE TABLE if not exists `{tablename}` (
      `id` char(66) CHARACTER SET ascii NOT NULL,
      `ts` int(11) DEFAULT NULL,
      `block` int(11) DEFAULT NULL,
      `from` char(42) CHARACTER SET ascii DEFAULT NULL,
      `to` char(42) CHARACTER SET ascii DEFAULT NULL,
      `nonce` int(11) DEFAULT NULL,
      `data` varchar(50000) CHARACTER SET ascii DEFAULT NULL,
      `txreceipt_status` smallint(6) DEFAULT NULL,
      `gaslimit` int(11) DEFAULT NULL,
      `gasused` int(11) DEFAULT NULL,
      `gasprice` bigint(11) DEFAULT NULL,
      PRIMARY KEY (`id`),
      KEY `from` (`from`),
      KEY `to` (`to`)
    ) ENGINE=InnoDB DEFAULT CHARSET=latin1"""
    return runsql(sql)

def createtable_pid_project(tablename):
    sql = f"""CREATE TABLE if not exists `{tablename}` (
      `blockid` int(11) NOT NULL,
      `tx10` char(10) NOT NULL,
      `user` char(42) DEFAULT NULL,
      `pid` int(11) DEFAULT NULL,
      `amount` bigint(11) DEFAULT NULL,
      PRIMARY KEY (`blockid`,`tx10`),
      KEY `user` (`user`),
      KEY `pid` (`pid`),
      KEY `user_2` (`user`,`pid`)
    ) ENGINE=InnoDB DEFAULT CHARSET=latin1"""
    return runsql(sql)

def fetchaddress(addr, oldres=None, toblock=None, onlyfirst=False, endpoint="api.bscscan.com", APIKEY=BSC_SCANKEY, tablename="tx", targetblock=None):
    page = 1
    res = oldres if oldres else []
    shouldcontinue = True
    while page<=10:
        d = scan_txlist(addr, page=page, toblock=toblock, endpoint=endpoint, APIKEY=APIKEY)
        minblock = min([int(i["blockNumber"]) for i in d]) if d else -1
        print(f"fetch page{page} len{len(d)} minblock{minblock}")
        if not d:
            shouldcontinue = False
            break
        sql = f"replace into {tablename}(`id`,`ts`,`block`,`from`,`to`,nonce,data,txreceipt_status,gaslimit,gasused,gasprice) values "
        items=[]
        for i in d:
            try:
                item = [i["hash"],i["timeStamp"],i["blockNumber"],i["from"],i["to"],i["nonce"],i["input"],i["txreceipt_status"],i["gas"],i["gasUsed"],i["gasPrice"]]
                res.append(item)
            except:
                print(i)
                raise
            sql += "(" + ("%s,"*len(item))[:-1] + "),"
            items.extend(item)
        runsql(sql[:-1], items)
        page += 1
        if onlyfirst or (targetblock and min([int(i[2]) for i in res])<targetblock ):
            return res
    if shouldcontinue:
        return fetchaddress(addr, oldres=res, toblock=min([int(i[2]) for i in res])+1, endpoint=endpoint, APIKEY=APIKEY, tablename=tablename)
    return res

def batch_callRPC(data, urls=BSC_NODES, retry=3, checkfunc=None, endpoint=None):
    if endpoint:
        urls = [endpoint]
        url = endpoint
    else:
        url = urls[0]
    try:
        x = sess.post(url, json=data, timeout=10)
        res = x.json()
        if checkfunc:
            checkfunc(res)
    except Exception as e:
        print(e)
        if retry:
            random.shuffle(urls)
            return batch_callRPC(data, urls=urls, retry=retry-1, checkfunc=checkfunc, endpoint=endpoint)
        else:
            raise
    return res

def batch_getTransactionCount(addrs, endpoint=None):
    data=[]
    for addr in addrs:
        data.append({"jsonrpc":"2.0","method":"eth_getTransactionCount","params": [addr,"latest"],"id":len(data)})
    res = batch_callRPC(data, endpoint=endpoint)
    #print(res)
    return [toi(i["result"]) for i in res]

def batch_getTransactionReceipt(txs, endpoint=None):
    data = []
    for tx in txs:
        data.append({"jsonrpc":"2.0","method":"eth_getTransactionReceipt","params": [tx],"id":len(data)})
    res = batch_callRPC(data, endpoint=endpoint)
    return [i["result"] for i in res]

def D(i, j=None):
    if j:
        return Decimal(int(i, j))
    else:
        return Decimal(i)

def lppool_value_pure(lpinfo, lptotal, myamount_nodecimal, token1_nodecimal_price=None, token2_nodecimal_price=None):
    if token1_nodecimal_price:
        pool_total_value = Decimal(int(lpinfo[:64],16)) * token1_nodecimal_price * 2
    else:
        assert token2_nodecimal_price, "should provide at least one price, example: token2_nodecimal_price=Decimal(1)/10**18"
        pool_total_value = Decimal(int(lpinfo[64:64*2],16)) * token2_nodecimal_price * 2
    myvalue = myamount_nodecimal/lptotal * pool_total_value
    return myvalue

def lppool_value(ENDPOINT, lpcontract, myamount_nodecimal, token1_nodecimal_price=None, token2_nodecimal_price=None):
    (_, lpinfo), (_,lptotal) = batch_callfunction(ENDPOINT, [[lpcontract, "getReserves()", ""], [lpcontract, "totalSupply()", ""]], "latest")
    lpinfo = lpinfo[2:]
    lptotal = D(lptotal, 16)
    #lpinfo = callfunction(ENDPOINT, lpcontract, "getReserves()", "", "latest", False)[2:]
    #lptotal = Decimal(callfunction(ENDPOINT, lpcontract, "totalSupply()", "", "latest"))
    return lppool_value_pure(lpinfo, lptotal, myamount_nodecimal, token1_nodecimal_price=token1_nodecimal_price, token2_nodecimal_price=token2_nodecimal_price)


def eth_getLogs(w3, _from, to, address=None, topics=["0x577a37fdb49a88d66684922c6f913df5239b4f214b2b97c53ef8e3bbb2034cb5"]):
    print("eth_getLogs", _from, to)
    conf = {
        "fromBlock": hex(_from),
        "toBlock": hex(to),
        "topics":topics
    }
    if address:
        conf['address']=w3.toChecksumAddress(address)
    data=w3.eth.getLogs(conf)
    return data