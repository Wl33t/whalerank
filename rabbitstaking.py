from base import *
STAKING_CONTRACT = "0x81c1e8a6f8eb226aa7458744c5e12fc338746571"
BANK="0xc18907269640d11e2a91d7204f33c5115ce3419e"

if 1:
    N = callfunction(B, STAKING_CONTRACT, "poolLength()", "")
    x = batch_callfunction(B, [[STAKING_CONTRACT, "poolInfo(uint256)", hex(i)[2:].rjust(64,"0")] for i in range(N)], "latest")
    tokens = ["0x"+i[1][2:66][-40:] for i in x]
    x2 = batch_callfunction(B, [[addr, "decimals()", ""] for addr in tokens], "latest")
    decimals = [int(i[1], 16) for i in x2]
    names = batch_callfunction_decode(B, [[addr, "name()", ""] for addr in tokens], ["string"])
    #exit(0)
else:
    decimals = [18]*48
    names = ['ibBNB', 'ibBUSD', 'ibUSDT', 'ibBTCB', 'ibETH', 'debtPancakeBUSD-USDT', 'debtPancakeBNB-BUSD', 'debtPancakeUSDT-BNB', 'debtPancakeETH-BNB', 'debtPancakeBTCB-BUSD', 'debtMdexBUSD-USDT', 'debtMdexBNB-BUSD', 'debtMdexUSDT-BNB', 'debtMdexBTCB-BUSD', 'debtMdexETH-BNB', 'MDEX LP Token', 'ibRABBIT', 'ibMDX', 'ibCAKE', 'debtPancakeBTCB-BNB', 'debtPancakeCAKE-BNB', 'debtMdexBTCB-BNB', 'debtMdexMDX-BNB', 'debtMdexBTCB-USDT', 'debtMdexETH-USDT', 'debtMdexETH-BTCB', 'ibLINK', 'ibXVS', 'ibDOT', 'ibUNI', 'ibLTC', 'ibFIL', 'ibADA', 'debtPancakeLINK-BNB', 'debtPancakeXVS-BNB', 'debtPancakeDOT-BNB', 'debtPancakeADA-BNB', 'debtPancakeUNI-BNB', 'debtPancakeCAKE-BUSD', 'debtMdexCAKE-BNB', 'debtMdexLTC-USDT', 'debtMdexMDX-BUSD', 'debtMdexADA-USDT', 'debtMdexFIL-USDT', 'debtMdexDOT-USDT', 'MDEX LP Token', 'debtPancakeRabbit-BNB', 'debtMdexRabbit-BUSD']

fetchaddress(STAKING_CONTRACT, onlyfirst=True)
txs = runsql("SELECT * FROM `tx` WHERE `to` = '0x81c1e8a6f8eb226aa7458744c5e12fc338746571' and (data like '0x0efe6a8b%%' or data like '0xb5c5f672%%') and txreceipt_status=1 order by block desc")
res = []
sql = "replace into rabbitstaking(`blockid`,tx10,user,pid,amount) values "
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
runsql(sql, res)
