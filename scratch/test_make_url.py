from sqlalchemy.engine.url import make_url

url = "postgresql://postgres.sbpllmzpnuheyptcdgbw:Master#23ATSmart30@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"
parsed = make_url(url)
print("Password:", parsed.password)
print("Host:", parsed.host)
print("Port:", parsed.port)
print("Database:", parsed.database)
