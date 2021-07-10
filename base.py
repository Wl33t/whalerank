import time, requests, hashlib, random, json, os, subprocess, sys, threading, traceback, pickle, math
from datetime import datetime
from decimal import Decimal
from base64 import b16decode, b16encode
from time import sleep
from copy import deepcopy
from collections import Counter
from runsql import *
from config import BSC_SCANKEY
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
def function_hash(func_str):
    return keccak.new(digest_bits=256).update(func_str.encode("utf-8")).hexdigest()[:8]
    
def addrtoarg(addr):
    if addr.startswith("0x"):
        addr = addr[2:]
    return addr.lower().rjust(64, "0")

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
    x = sess.post(endpoint, json=data, timeout=5)
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

def eth_getBlockByNumber(height, urls=BSC_NODES, retry=3):
    url = urls[0]
    if isinstance(height, int):
        height = hex(height)
    res = {}
    try:
        x = sess.post(url, data='{"id":%d,"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["%s",true]}'%(random.randint(0,9999),height), timeout=5)
        res = x.json()["result"]
    except:
        pass
    if "transactions" not in res:
        if retry:
            sleep(2)
            random.shuffle(urls)
            print("change api to", urls[0])
            return eth_getBlockByNumber(height, urls=urls, retry=retry-1)
        else:
            raise Exception(x.text)
    return res

def batch_eth_getBlockByNumber(heights):
    data = []
    for height in heights:
        if isinstance(height, int):
            height = hex(height)
        data.append({"id":len(data),"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":[height,True]})
    def f(res):
        assert res and "transactions" in res[0]["result"]
    res = batch_callRPC(data, checkfunc=f)
    return [i["result"] for i in res]

def fetchaddress(addr, oldres=None, toblock=None, onlyfirst=False):
    page = 1
    res = oldres if oldres else []
    shouldcontinue = True
    while page<=10:
        d = scan_txlist(addr, page=page, toblock=toblock)
        minblock = min([int(i["blockNumber"]) for i in d]) if d else -1
        print(f"fetch page{page} len{len(d)} minblock{minblock}")
        if not d:
            shouldcontinue = False
            break
        sql = "replace into tx(`id`,`ts`,`block`,`from`,`to`,nonce,data,txreceipt_status,gaslimit,gasused,gasprice) values "
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
        if onlyfirst:
            return res
    if shouldcontinue:
        return fetchaddress(addr, oldres=res, toblock=min([int(i[2]) for i in res])+1)
    return res

def batch_callRPC(data, urls=BSC_NODES, retry=3, checkfunc=None):
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
            return batch_callRPC(data, urls=urls, retry=retry-1, checkfunc=checkfunc)
        else:
            raise
    return res

def batch_getTransactionCount(addrs):
    data=[]
    for addr in addrs:
        data.append({"jsonrpc":"2.0","method":"eth_getTransactionCount","params": [addr,"latest"],"id":len(data)})
    res = batch_callRPC(data)
    return [toi(i["result"]) for i in res]

def batch_getTransactionReceipt(txs):
    data = []
    for tx in txs:
        data.append({"jsonrpc":"2.0","method":"eth_getTransactionReceipt","params": [tx],"id":len(data)})
    res = batch_callRPC(data)
    return [i["result"] for i in res]

def D(i, j=None):
    if j:
        return Decimal(int(i, j))
    else:
        return Decimal(i)

