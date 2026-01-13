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
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
      "https://auth-client-eight.vercel.app"  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        
    allow_credentials=True,
    allow_methods=["*"],         
    allow_headers=["*"],         
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
   

 