import os
from typing import Optional
import bcrypt
import datetime
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from google_auth import create_access_token
from model.config import conn 
from psycopg2 import Error, pool
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from model.users import create_users



router = APIRouter()
app = FastAPI()

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

pg_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("GOOGLE_SECRET_KEY"))
GOOGLE_CLIENT_ID =  os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET =  os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY =  os.getenv("GOOGLE_SECRET_KEY")



limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


config_data = {
    "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
    "SECRET_KEY": SECRET_KEY,
}
config = Config(environ=config_data)
oauth = OAuth(config)

google = oauth.register(
    name="google",
    client_id=config_data["GOOGLE_CLIENT_ID"],
    client_secret=config_data["GOOGLE_CLIENT_SECRET"],
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "openid email profile"},
)
class UserSignup(BaseModel):
    email: str
    password: str
    name: Optional[str]


class UserLogin(BaseModel):
    email: str
    password: str


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/signup")
def create_new_user(user: UserSignup):
    conn = None
    try:
        conn = pg_pool.getconn()
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users(email, password, username) VALUES (%s, %s, %s)",
                (user.email, hashed_password, user.name)
            )
            conn.commit()
        return {"status": "success", "message": "User created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            pg_pool.putconn(conn)


@router.post("/login")
# @limiter.limit("5/minute") 
def login(user: UserLogin, request: Request):
    conn = None
    try:
        conn = pg_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (user.email,))
            user_record = cur.fetchone()

            if not user_record:
                return {"status": "fail", "message": "Invalid email or password"}

            if user_record[4] is True or user_record[3] is None:
                return {
                    "status": "fail", 
                    "message": "This account uses Google Sign-In. Please use the 'Sign in with Google' button."
                }

            stored_hash_value = user_record[3]
            stored_hash = (
                stored_hash_value.tobytes()
                if hasattr(stored_hash_value, 'tobytes')
                else bytes.fromhex(stored_hash_value[2:])
            )

            user_input_password = user.password.encode('utf-8')
            if bcrypt.checkpw(user_input_password, stored_hash):
                access_token = create_access_token(
                    data={"sub": str(user_record[0])},
                    expires_delta=datetime.timedelta(minutes=60)
                )

                return {
                    "status": "success",
                    "message": "Login successful",
                    "token": access_token
                }
            else:
                return {"status": "fail", "message": "Invalid email or password"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            pg_pool.putconn(conn)



@router.get("/user")
def get():
    conn = None
    try:
        conn = pg_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users")
            user_record = cur.fetchall()
            return {
                    "status": "success",
                    "message": "Login successful",
                    "users": user_record
        }       
          
           
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            pg_pool.putconn(conn)




@router.get("/user/{email}")
def get_user(email: str):
    conn = None
    try:
        conn = pg_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            cur.execute(
                """
                SELECT id, email, username, profile_picture, 
                       is_google_user, mfa_enabled, created_at
                FROM users
                WHERE email = %s
                """,
                (email,)
            )
            user_record = cur.fetchone()

            if not user_record:
                raise HTTPException(status_code=404, detail="User not found")

            return {
                "status": "success",
                "message": "User retrieved successfully",
                "user": user_record
            }

    finally:
        if conn:
            pg_pool.putconn(conn)




@router.post("/delete")
def delete_user(user: UserLogin):
    conn = None
    try:
        conn = pg_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (user.email,))
            user_record = cur.fetchone()

            if not user_record:
                return {"status": "fail", "message": "User not found"}
            
            stored_hash_value = user_record[3]
            
            if stored_hash_value is None:
                return {"status": "fail", "message": "Cannot delete Google accounts this way"}
            
            stored_hash = (
                stored_hash_value.tobytes()
                if hasattr(stored_hash_value, 'tobytes')
                else bytes.fromhex(stored_hash_value[2:])
            )
            
            if bcrypt.checkpw(user.password.encode('utf-8'), stored_hash):
                cur.execute("DELETE FROM users WHERE email = %s", (user.email,))
                conn.commit()
                return {"status": "success", "message": "User deleted successfully"}
            else:
                return {"status": "fail", "message": "Invalid credentials"}
                
    except Exception as e:
        return {"status": "error", "message": "An error occurred"}
    finally:
        if conn:
            pg_pool.putconn(conn)
