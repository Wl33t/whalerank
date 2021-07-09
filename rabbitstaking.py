from base import *

from alpacastaking import *
if __name__ == "__main__":
    STAKING_CONTRACT = "0x81c1e8a6f8eb226aa7458744c5e12fc338746571"
    BANK="0xc18907269640d11e2a91d7204f33c5115ce3419e"
    TABLENAME= "rabbitstaking"
    names = ['ibBNB', 'ibBUSD', 'ibUSDT', 'ibBTCB', 'ibETH', 'debtPancakeBUSD-USDT', 'debtPancakeBNB-BUSD', 'debtPancakeUSDT-BNB', 'debtPancakeETH-BNB', 'debtPancakeBTCB-BUSD', 'debtMdexBUSD-USDT', 'debtMdexBNB-BUSD', 'debtMdexUSDT-BNB', 'debtMdexBTCB-BUSD', 'debtMdexETH-BNB', 'MDEX LP Token', 'ibRABBIT', 'ibMDX', 'ibCAKE', 'debtPancakeBTCB-BNB', 'debtPancakeCAKE-BNB', 'debtMdexBTCB-BNB', 'debtMdexMDX-BNB', 'debtMdexBTCB-USDT', 'debtMdexETH-USDT', 'debtMdexETH-BTCB', 'ibLINK', 'ibXVS', 'ibDOT', 'ibUNI', 'ibLTC', 'ibFIL', 'ibADA', 'debtPancakeLINK-BNB', 'debtPancakeXVS-BNB', 'debtPancakeDOT-BNB', 'debtPancakeADA-BNB', 'debtPancakeUNI-BNB', 'debtPancakeCAKE-BUSD', 'debtMdexCAKE-BNB', 'debtMdexLTC-USDT', 'debtMdexMDX-BUSD', 'debtMdexADA-USDT', 'debtMdexFIL-USDT', 'debtMdexDOT-USDT', 'MDEX LP Token', 'debtPancakeRabbit-BNB', 'debtMdexRabbit-BUSD']
    if os.environ.get("FULL", False):
        fetchaddress(STAKING_CONTRACT, onlyfirst=False)
    update_alpaca_fairlaunch(STAKING_CONTRACT, TABLENAME, updatedecimals=True)