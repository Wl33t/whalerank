from momo import update_generic, os, fetchaddress, MATIC_SCANKEY
STAKING_CONTRACT="0x1fd1259fa8cdc60c6e8c86cfa592ca1b8403dfad"
deposit_PREFIXs, withdraw_PREFIXs=["0x8dbdbe6d"], ["0x0ad58d2f", "0xd1abb907"]
pid_from_data = lambda data:int(data[10:10+64],16)
amount_from_data = lambda data:int(data[10+64:10+64*2],16)
user_from_data = lambda data:"0x"+data[-40:]


def update_maticiron(force=False):
    fetchaddress(STAKING_CONTRACT, onlyfirst=True, endpoint="api.polygonscan.com", APIKEY=MATIC_SCANKEY, tablename="matictx")
    def pid2decimal(pid):
        if pid==0:
            return 18-6
        else:
            return 18-12
    update_generic("maticiron", STAKING_CONTRACT, deposit_PREFIXs, withdraw_PREFIXs, pid_from_data, amount_from_data, user_from_data=user_from_data, txtable="matictx", pid2decimal=pid2decimal, force=force)

if __name__ == "__main__":
    if not os.environ.get("SKIP", False):
        update_maticiron(force=os.environ.get("FORCE",False))