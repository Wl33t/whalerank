import sys
sys.path.append("..")
from base import *
STAKING_CONTRACT="0xdad49e63f97c967955975490a432de3796c699e6"
deposit_PREFIX, withdraw_PREFIX="0xe2bbb158", "0x441a3e70"
pid_from_data = lambda data:int(data[10:10+64],16)
amount_from_data = lambda data:int(data[10+64:],16)
deposit_id2prefix = lambda i:deposit_PREFIX+hex(i)[2:].rjust(64,"0")

TABLENAME="momo"

def lpaddress2symbols(lpaddress):
    token0, token1 = batch_callfunction_decode(B, [[lpaddress, "token0()", ""], [lpaddress, "token1()", ""]], ["address"])
    symbol0, symbol1 = batch_callfunction_decode(B, [[token0, "symbol()", ""], [token1, "symbol()", ""]], ["string"])
    return symbol0, symbol1

TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def search_id2tokenname(id):
    p = deposit_id2prefix(id)
    data = runsql(f"SELECT * FROM `tx` WHERE `to` = '{STAKING_CONTRACT}' and data like '{p}%%' and txreceipt_status=1 order by block desc limit 1")
    if not data:
        return
    tx = data[0][0]
    x = batch_getTransactionReceipt([tx])[0]
    lp=[i for i in x["logs"] if i["topics"][0]==TOPIC_TRANSFER and x["from"][2:] in i["topics"][1]][0]["address"]
    name = batch_callfunction_decode(B, [[lp, "symbol()", ""]], ["string"])[0]
    if name=="Cake-LP":
        symbol0, symbol1 = lpaddress2symbols(lp)
        name = symbol0+"-"+symbol1
    return name, lp

def search_iter():
    res = {}
    failcnt = 0
    for i in range(100):
        r = search_id2tokenname(i)
        if not r:
            failcnt += 1
            if failcnt>3:#we stop when we fail three times in a row
                break
            else:
                continue
        failcnt=0
        name,addr = r
        res[i]=(name, addr)
        print(i, name, addr)
    return res

def update_momo():
    fetchaddress(STAKING_CONTRACT, onlyfirst=True)
    update_generic(TABLENAME=TABLENAME, STAKING_CONTRACT=STAKING_CONTRACT, deposit_PREFIX=deposit_PREFIX, withdraw_PREFIX=withdraw_PREFIX, 
        pid_from_data=pid_from_data, amount_from_data=amount_from_data, user_from_data=None, txtable="tx", pid2decimal=None)

def update_generic(TABLENAME, STAKING_CONTRACT, deposit_PREFIX, withdraw_PREFIX, pid_from_data, amount_from_data, user_from_data=None, txtable="tx", pid2decimal=None, force=False):
    sql = f"SELECT * FROM `{txtable}` WHERE `to` = '{STAKING_CONTRACT}' and (data like '{deposit_PREFIX}%%' or data like '{withdraw_PREFIX}%%') and txreceipt_status=1 order by block desc"
    try:
        if not force:
            startblockid = int(runsql(f"select max(blockid) from {TABLENAME}")[0][0])
            sql = sql.replace(" order by", f" and block>={startblockid} order by")
    except:
        traceback.print_exc()
    txs = runsql(sql)
    print("txs:", len(txs))
    res = []
    sql = sqlprefix = f"replace into {TABLENAME}(`blockid`,tx10,user,pid,amount) values "
    for hash,ts,blockid,user,to,nonce,data,_,gaslimit,gasused,gasprice in txs:
        tx10 = hash[2:12]
        #print(data)
        pid = pid_from_data(data)
        amount = amount_from_data(data)
        if data.startswith(withdraw_PREFIX):
            amount = -amount
        if pid2decimal: #how many decimals should we drop? 
            dropdecimal = pid2decimal(pid)
        else: # for usd pools, we recommend keep 6 digits, so drop 18-6 decimal
            dropdecimal = 18-6
        amount //= 10**dropdecimal
        if user_from_data:
            user = user_from_data(data)
        item= [blockid, tx10, user, pid, amount]
        res.extend(item)
        sql += "(" + ("%s,"*len(item))[:-1] + "),"
        if len(res)>1000:
            runsql(sql, res)
            sql = sqlprefix
            res = []
    if res:
        runsql(sql, res)
    print("done")

if __name__ == "__main__":
    if not os.environ.get("SKIP", False):
        update_momo()