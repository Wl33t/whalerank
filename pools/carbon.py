import sys
sys.path.append("..")
from base import *
from runsql import *
from web3 import Web3
STAKING_CONTRACT="0x27F0408729dCC6A4672e1062f5003D2a07E4E10D"
w3 = Web3(Web3.HTTPProvider(ARBI))
end = w3.eth.blockNumber

TABLENAME = "carbon"
start = 486372
try:
    start = int(runsql(f"select max(blockid) from {TABLENAME}")[0][0])
except:
    pass

print("total blocks:", end-start)
res = []
Staked = event_hash("Staked(address,uint256)")
Withdrawn = event_hash("Withdrawn(address,uint256)")
topic2type = {Staked: 1, Withdrawn:-1}
BLOCK_BATCH = 1000
while start<end:
    items = eth_getLogs(w3, start, start+BLOCK_BATCH, STAKING_CONTRACT, topics=["0x"+Staked])+\
                     eth_getLogs(w3, start, start+BLOCK_BATCH, STAKING_CONTRACT, topics=["0x"+Withdrawn])
    start += BLOCK_BATCH
    if not items:
        continue
    start += BLOCK_BATCH
    if not items:
        continue
    sql = f"replace into {TABLENAME}(blockid, logindex, `user`, pid, amount) values"
    pending = []
    for log in items:
        blockid = log.blockNumber
        logindex = log.logIndex
        user = "0x"+log.topics[1].hex()[-40:]
        pid = 0
        amount = int(log.data, 16)
        amount *= topic2type[log.topics[0].hex()[2:]]
        x = [blockid, logindex, user, pid, amount]
        sql += "(%s"+",%s"*(len(x)-1)+"),"
        pending.extend(x)
    runsql(sql, pending)
