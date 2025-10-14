from fastapi import FastAPI
from routers.powerbi import router as powerbi_router

app = FastAPI()
app.include_router(powerbi_router)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
