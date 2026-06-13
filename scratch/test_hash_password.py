import os
from sqlmodel import create_engine

url = "postgresql://postgres.sbpllmzpnuheyptcdgbw:Master#23ATSmart30@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"

is_valid_db_url = True

try:
    test_connect_args = {"connect_timeout": 3}
    temp_engine = create_engine(url, connect_args=test_connect_args)
    print("Created engine. Connecting...")
    with temp_engine.connect() as conn:
        print("Connected successfully?!")
except Exception as e:
    print("Caught connection error:")
    print(type(e), str(e))
    is_valid_db_url = False

print("is_valid_db_url is now:", is_valid_db_url)
