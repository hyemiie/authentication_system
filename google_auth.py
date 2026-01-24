import os
import jwt
import datetime
import httpx
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from model.config import conn
import urllib.parse
import json


router = APIRouter(tags=["google-auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 

ALLOWED_COMPANY_URLS = {
    "https://git-chat.vercel.app",
    "http://localhost:3000",
    "https://gitxen-zq9s.vercel.app",
    "https://auth-client-eight.vercel.app/"
}

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



@router.get("/google/login")
async def google_login(company_url: str):
    if company_url not in ALLOWED_COMPANY_URLS:
        raise HTTPException(status_code=400, detail="Invalid company URL")

    state_payload = {
        "company_url": company_url
    }

    state = urllib.parse.quote(json.dumps(state_payload))

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        "scope=openid email profile&"
        "response_type=code&"
        f"state={state}&"
        "access_type=offline&"
        "prompt=consent"
    )

    return RedirectResponse(url=google_auth_url)


@router.get("/auth/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None
):
    if error:
        raise HTTPException(status_code=400, detail=error)

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    try:
        state_data = json.loads(urllib.parse.unquote(state))
        company_url = state_data["company_url"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state")

    if company_url not in ALLOWED_COMPANY_URLS:
        raise HTTPException(status_code=400, detail="Unapproved client")

    token_response = await httpx.AsyncClient().post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        },
    )

    token_json = token_response.json()


    if "access_token" not in token_json:
        return RedirectResponse(f"{company_url}/auth?error=token_exchange_failed")

    access_token = token_json["access_token"]

    user_response = await httpx.AsyncClient().get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    user_info = user_response.json()
    if "email" not in user_info:
        return RedirectResponse(f"{company_url}/auth?error=userinfo_failed")

    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])
    google_id = user_info.get("id")
    picture = user_info.get("picture")

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user:
            cur.execute(
                """UPDATE users SET username=%s, google_id=%s, profile_picture=%s
                   WHERE email=%s RETURNING id, username, email""",
                (name, google_id, picture, email),
            )
        else:
            cur.execute(
                """INSERT INTO users (email, username, google_id, is_google_user, profile_picture)
                   VALUES (%s, %s, %s, true, %s)
                   RETURNING id, username, email""",
                (email, name, google_id, picture),
            )

        user_record = cur.fetchone()
        conn.commit()

    jwt_token = create_access_token({
        "sub": email,
        "user": {
            "id": user_record[0],
            "username": user_record[1],
            "email": user_record[2],
            "is_google_user": True,
            "profile_picture": picture,
        }
    })

    return RedirectResponse(f"{company_url}/auth?token={jwt_token}")
