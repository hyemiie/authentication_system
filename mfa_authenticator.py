# from fastapi.responses import JSONResponse
# import pyotp
# import qrcode
# import os
# from fastapi import APIRouter, HTTPException
# from model.config import conn

# router =  APIRouter()

 
# def init_db():
#     conn.commit()
#     conn.close()



# def create_user_secret(email):
#     secret = pyotp.random_base32()
#     print(f"Generated secret for {email}: {secret}")

#     cur = conn.cursor()
#     cur.execute(
#         "INSERT INTO users (email, user_secret) VALUES (%s, %s)",
#         (email, secret),
#     )
#     conn.commit()

#     return secret


# def create_qr_code(email):
#     cur = conn.cursor()
#     cur.execute("SELECT user_secret FROM users WHERE email = %s", (email,))
#     row = cur.fetchone()
#     conn.close()

#     if not row:
#         raise ValueError("User not found in database")

#     user_secret = row[0]  
#     issuer_name = "MyApp"
#     uri = pyotp.TOTP(user_secret).provisioning_uri(
#         name=email, issuer_name=issuer_name
#     )

#     filename = f"{email}_mfa_qr.png"
#     qrcode.make(uri).save(filename)
#     print(f"✅ QR code saved as {filename}. Scan it with Google or Microsoft Authenticator.")
#     return uri


# @router.post("/setup_MFA")
# def setup_mfa(email):
#     try:
#         user_secret = create_user_secret(email)
#         if user_secret:
#             try:
#                 code = create_qr_code(email)
#             except Exception as e:
#                 raise HTTPException(status_code=400, detail=str(e))
#         else:
#             return JSONResponse("secret not created")
#         return code
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
        


# def verify_code(email, user_code):
#     cur = conn.cursor()
#     cur.execute("SELECT user_secret FROM users WHERE email = ?", (email,))
#     row = cur.fetchone()
#     conn.close()

#     if not row:
#         raise ValueError("User not found in database")

#     user_secret = row[0]  
#     totp = pyotp.TOTP(user_secret)

#     if totp.verify(user_code):
#         print("✅ Verified!")
#         return True
#     else:
#         print("❌ Invalid code")
#         return False


# if __name__ == "__main__":
#     init_db()

#     email = "user@example.com"

#     if not os.path.exists("users.db"):
#         init_db()
#     create_user_secret(email)

#     create_qr_code(email)

#     code = input("Enter the code from your app: ")
#     verify_code(email, code)



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
            
            # for i in range(-2, 3):
            #     import time
            #     test_time = time.time() + (i * 30)
            #     test_code = totp.at(test_time)
            #     print(f"Window {i}: {test_code}")

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