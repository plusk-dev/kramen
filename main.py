import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from exception_handler import error_500
from utils.notifs.admin.discord import send_discord_message

from dungo.auth import auth_router
from dungo.integrations import integrations_router
from dungo.api_key import api_key_router
from dungo.payments import payments_router

from rag.identify_endpoints import run_query_router

app = FastAPI(title="Kramen API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    return {}


async def on_startup():
    print(os.getenv("DATABASE_URL"))
    send_discord_message("start-shut", "success", "App Started")


async def on_shutdown():
    send_discord_message("start-shut", "info", "App Shutdown")


app.include_router(auth_router, prefix="/auth", tags=['Auth'])
app.include_router(integrations_router,
                   prefix="/integrations", tags=['Integrations'])
app.include_router(api_key_router, prefix="/keys", tags=['API Keys'])
app.include_router(payments_router, prefix="/payments", tags=['Payments'])
app.include_router(run_query_router, prefix="/run", tags=['Run'])

app.add_event_handler("startup", on_startup)
app.add_event_handler("shutdown", on_shutdown)
app.add_exception_handler(500, error_500)
