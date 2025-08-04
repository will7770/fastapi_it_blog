from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.database.core import get_session, get_db
from src.api.dependencies import get_current_user, mod_access


async def admin_protection_middleware(request: Request, call_next):
    if not request.url.path.startswith("/admin"):
        return await call_next(request)

    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse(
            {"detail": "Missing authorization token"},
            status_code=401
        )

    try:
        async with get_db() as session:
            user = await get_current_user(request, session=session)
            is_mod_or_above = await mod_access(user=user)

            if not is_mod_or_above:
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
        return await call_next(request)

    except HTTPException as e:
        return JSONResponse(
            {"detail": str(e.detail)},
            status_code=e.status_code
        )