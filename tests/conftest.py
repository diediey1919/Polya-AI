import os

# Ensure tests have default environment variables configured if not set in caller environment
if not os.environ.get("POLYA_AUTH_SECRET"):
    os.environ["POLYA_AUTH_SECRET"] = "9fa39ef1c06ca08ed58247873d25ef2d29c52c88235203ac786ecbd0bac35ff9"
if not os.environ.get("POLYA_DB_PATH"):
    os.environ["POLYA_DB_PATH"] = "/home/ubuntu/.polya/polya_index.db"
