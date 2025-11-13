from fastapi import FastAPI, Request
 
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
from routers.panelDetail import router as panelDetail
from routers.editPanel import router as editPanel
from routers.media_uploads import router as media_router, mount_media
 
# ___________________________________________
 
 
app = FastAPI()
 
# static em /static
app.mount("/static", StaticFiles(directory="static"), name="static")

#monta /media a partir do NFS (/data/media)
mount_media(app) 
 
@app.middleware("http")
async def csp_upgrade(request: Request, call_next):
    resp = await call_next(request)
    # promove http->https e bloqueia mixed content ativo
    resp.headers["Content-Security-Policy"] = \
        "upgrade-insecure-requests; block-all-mixed-content"
    return resp
 
 
app.include_router(powerbi_router)
app.include_router(admin )
app.include_router(auth)
app.include_router(index)
app.include_router(reports)
app.include_router(userRegistrationGroup)
app.include_router(reportRegistrationGroup)
app.include_router(grupoView)
app.include_router(userRegister)
app.include_router(panelDetail)
app.include_router(media_router)
app.include_router(editPanel)
 
 
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nieshml.saude.sp.gov.br"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)