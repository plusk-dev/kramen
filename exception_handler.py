from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from utils.notifs.admin.discord import send_discord_message


async def error_500(request: Request, error: HTTPException):
    print(dict(request.headers))
    send_discord_message(
        "err", "danger", f"Something broke ```{request.url} \n{error}```")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "The server has gotten itself into trouble.",
        },
    )
