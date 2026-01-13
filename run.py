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

create_users(conn=conn)