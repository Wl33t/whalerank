from base import *

def update_alpaca_fairlaunch(STAKING_CONTRACT, TABLENAME, updatedecimals=True):
    if updatedecimals:
        N = callfunction(B, STAKING_CONTRACT, "poolLength()", "")
        x = batch_callfunction(B, [[STAKING_CONTRACT, "poolInfo(uint256)", hex(i)[2:].rjust(64,"0")] for i in range(N)], "latest")
        tokens = ["0x"+i[1][2:66][-40:] for i in x]
        x2 = batch_callfunction(B, [[addr, "decimals()", ""] for addr in tokens], "latest")
        decimals = [int(i[1], 16) for i in x2]
        names = batch_callfunction_decode(B, [[addr, "name()", ""] for addr in tokens], ["string"])
        #exit(0)
    else:
        decimals = [18]*100
        
    fetchaddress(STAKING_CONTRACT, onlyfirst=True)
    sql = f"SELECT * FROM `tx` WHERE `to` = '{STAKING_CONTRACT}' and (data like '0x0efe6a8b%%' or data like '0xb5c5f672%%') and txreceipt_status=1 order by block desc"
    try:
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
        pid = int(data[10+64:10+64*2],16)
        amount = int(data[10+64*2:], 16)
        if data.startswith("0xb5c5f672"):
            amount = -amount
        amount //= 10**(decimals[pid]-6) #we hold 6 digits after the decimal point
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
    STAKING_CONTRACT = "0xa625ab01b08ce023b2a342dbb12a16f2c8489a8f"
    TABLENAME= "alpacastaking"
    names = ['debtibBNB', 'Interest Bearing BNB', 'debtibBUSD', 'Interest Bearing BUSD', 'Pancake LPs', 'Stronk Alpaca', 'debtIbBNB_V2', 'debtIbBUSD_V2', 'debtibETH_V2', 'Interest Bearing ETH', 'debtibALPACA_V2', 
        'Interest Bearing ALPACA', 'Pancake LPs', 'debtibUSDT_V2', 'Interest Bearing USDT', 'debtibUSDT_V2', 'Interest Bearing USDT', 'debtibBTCB_V2', 'Interest Bearing BTCB']
    if os.environ.get("FULL", False):
        fetchaddress(STAKING_CONTRACT, onlyfirst=False)
    update_alpaca_fairlaunch(STAKING_CONTRACT, TABLENAME, updatedecimals=True)