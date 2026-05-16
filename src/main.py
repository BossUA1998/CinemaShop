from fastapi import FastAPI, Request, HTTPException, status
from starlette.responses import JSONResponse

from routes.accounts import router as accounts_router
from routes.movies import router as movies_router
from routes.cart import router as cart_router
from routes.orders import router as orders_router
from routes.payments import router as payments_router

app = FastAPI()


@app.middleware("http")
async def docs_middleware(request: Request, call_next):
    if request.url.path in {"/docs", "/redoc", "/openapi.json"}:
        from config.dependencies import get_jwt_manager, get_token, get_settings

        try:
            token = get_token(request)
            jwt_manager = get_jwt_manager(settings=get_settings())
            jwt_manager.decode_access_token(token=token)
        except HTTPException:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "You are not authorized"},
            )
    return await call_next(request)


app.include_router(accounts_router, prefix="/auth", tags=["auth"])
app.include_router(movies_router, prefix="/movies", tags=["movies"])
app.include_router(cart_router, prefix="/cart", tags=["cart"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])
app.include_router(payments_router, prefix="/payments", tags=["payments"])
