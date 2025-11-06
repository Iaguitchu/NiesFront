from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# __________________ Rotas __________________
from routers.powerbi import router as powerbi_router
from routers.admin import router as admin
from routers.auth import router as auth
from routers.index import router as index
from routers.reports import router as reports
from routers.userRegistrationGroup import router as userRegistrationGroup
from routers.reportRegistrationGroup import router as reportRegistrationGroup
from routers.grupoView import router as grupoView
from routers.userRegister import router as userRegister

# ___________________________________________


app = FastAPI()

# static em /static
app.mount("/static", StaticFiles(directory="static"), name="static")




app.include_router(powerbi_router)
app.include_router(admin )
app.include_router(auth)
app.include_router(index)
app.include_router(reports)
app.include_router(userRegistrationGroup)
app.include_router(reportRegistrationGroup)
app.include_router(grupoView)
app.include_router(userRegister)


from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
