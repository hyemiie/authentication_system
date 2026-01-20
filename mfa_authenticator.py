from fastapi.responses import JSONResponse
import pyotp
import qrcode
from io import BytesIO
import base64
from fastapi import APIRouter, HTTPException
from psycopg2 import pool
import os
from dotenv import load_dotenv
load_dotenv()
import datetime

router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")
pg_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)

@router.post("/setup_mfa")
def setup_mfa(email: str):
    conn = None
    try:
        conn = pg_pool.getconn()
        
        secret = pyotp.random_base32()
        
        with conn.cursor() as cur:
            cur.execute("SELECT id, user_secret FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # if user[1] is not None:
            #   raise HTTPException(status_code=409, detail="MFA is already setup")


            cur.execute(
                "UPDATE users SET user_secret = %s WHERE email = %s",
                (secret, email)
            )

            cur.execute(
                "UPDATE users SET mfa_enabled = True",
            )
            conn.commit()
        
        issuer_name = "MyAuthApp"
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=email, 
            issuer_name=issuer_name
        )
        
        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "status": "success",
            "qr_code": f"data:image/png;base64,{qr_base64}",
            # "secret": secret,  
            "uri": uri
        }
        
    except Exception as e:
        print("E", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            pg_pool.putconn(conn)



@router.post("/verify_mfa")
def verify_mfa(email: str, code: str):
    print("email", email, code)
    conn = None
    try:
        conn = pg_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT user_secret FROM users WHERE email = %s", (email,))
            row = cur.fetchone()

            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="MFA not set up for this user")

            user_secret = row[0]
            code = str(code).strip()
            
            totp = pyotp.TOTP(user_secret, digits=6, interval=30)
            print("totp", user_secret)
            
            is_valid = totp.verify(code, valid_window=1)

            if is_valid:
                return {
                    "status": "success",
                    "message": "Code verified successfully"
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid MFA code")
    finally:
        if conn:
            pg_pool.putconn(conn)


@router.get("/mfa_status/{email}")
def check_mfa_status(email: str):
    """Check if user has MFA enabled"""
    conn = None
    try:
        conn = pg_pool.getconn()
        
        with conn.cursor() as cur:
            cur.execute("SELECT user_secret FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "mfa_enabled": row[0] is not None,
                "email": email
            }
                
    finally:
        if conn:
            pg_pool.putconn(conn)