from fastapi import FastAPI, APIRouter
import mfa_authenticator
import user_controller
import google_auth
from model.config import conn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(mfa_authenticator.router)
app.include_router(user_controller.router)
app.include_router(google_auth.router)


origins = [
    "http://localhost:3000",  # frontend dev server
    "http://127.0.0.1:3000",  # sometimes needed
    # Add other allowed origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Or ["*"] for testing only
    allow_credentials=True,
    allow_methods=["*"],          # This is important: OPTIONS, GET, POST, etc.
    allow_headers=["*"],          # Allow Authorization and Content-Type
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
   

 