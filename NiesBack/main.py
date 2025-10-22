from fastapi import FastAPI
from routers.powerbi import router as powerbi_router
from routers.admin import router as admin
from routers.auth import router as auth

app = FastAPI()
app.include_router(powerbi_router)
app.include_router(admin )
app.include_router(auth)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
