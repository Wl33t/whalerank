from base import *
if os.environ.get("MATIC"):
    createtable_tx("matictx")
    fetchaddress(sys.argv[1], endpoint="api.polygonscan.com", APIKEY=MATIC_SCANKEY, tablename="matictx")
else:
    fetchaddress(sys.argv[1])