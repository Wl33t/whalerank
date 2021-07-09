from base import *
STAKING_CONTRACT="0xdad49e63f97c967955975490a432de3796c699e6"
deposit_PREFIX, withdraw_PREFIX="0xe2bbb158", "0x441a3e70"
pid_from_data = lambda data:int(data[10:10+64],16)
amount_from_data = lambda data:int(data[10+64:],16)
TABLENAME="momo"

fetchaddress(STAKING_CONTRACT, onlyfirst=True)
sql = f"SELECT * FROM `tx` WHERE `to` = '{STAKING_CONTRACT}' and (data like '{deposit_PREFIX}%%' or data like '{withdraw_PREFIX}%%') and txreceipt_status=1 order by block desc"
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
    pid = pid_from_data(data)
    amount = amount_from_data(data)
    if data.startswith(withdraw_PREFIX):
        amount = -amount
    amount //= 10**(18-6) #TODO: we have no abi for poolInfo, assuming all tokens has 18 decimals
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