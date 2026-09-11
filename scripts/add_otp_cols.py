import os, sys
sys.path.insert(0, r"c:/Users/Codewithme/jewelry-gh")
import psycopg2
conn = psycopg2.connect("dbname=aurum_ghana user=postgres password=DONK.COM0556922494 host=127.0.0.1 port=5432")
cur = conn.cursor()
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_otp_code VARCHAR(6)")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_otp_expires_at TIMESTAMP WITH TIME ZONE")
conn.commit()
print("columns added OK")
