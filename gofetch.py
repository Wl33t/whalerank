from base import *
if os.environ.get("MATIC"):
    createtable_tx("matictx")
    fetchaddress(sys.argv[1], endpoint="api.polygonscan.com", APIKEY=MATIC_SCANKEY, tablename="matictx")
elif os.environ.get("FTM"):
    createtable_tx("tx_ftm")
    fetchaddress(sys.argv[1], endpoint="api.ftmscan.com", APIKEY=FTM_SCANKEY, tablename="tx_ftm")
elif os.environ.get("ETH"):
    createtable_tx("ethtx")
    fetchaddress(sys.argv[1], endpoint="api.etherscan.io", APIKEY=ETH_SCANKEY, tablename="ethtx")
elif os.environ.get("ARBI"):
    createtable_tx("tx_arbi")
    fetchaddress(sys.argv[1], endpoint="api.arbiscan.io", APIKEY="", tablename="tx_arbi")
else:
    fetchaddress(sys.argv[1])
