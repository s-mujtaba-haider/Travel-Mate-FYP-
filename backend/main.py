import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi_another_jwt_auth import AuthJWT
from fastapi_another_jwt_auth.exceptions import AuthJWTException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from controller import ErrorResponse, RAGError
# from controller.database import Base, engine
from routes import auth_router, session_router, chat_router



# def create_tables():  # new
#     Base.metadata.create_all(bind=engine)


def include_router(app_instance):
    app_instance.include_router(auth_router)
    app_instance.include_router(session_router)
    app_instance.include_router(chat_router)


def start_application():
    app_instance = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    include_router(app_instance)
    # create_tables()  # new
    return app_instance


app = start_application()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("SECRET_KEY")


@AuthJWT.load_config
def get_config():
    return Settings()



@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

@app.exception_handler(RAGError)
async def rag_error_handler(request: Request, exc: RAGError):
    """Handle all RAG-related errors"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).dict()
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description="RAG Travel Mate API",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter: **'Bearer &lt;JWT&gt;'**, where JWT is the access token"
        }
    }

    # Get routes from index 4 because before that fastapi define router for /openapi.json, /redoc, /docs, etc
    # Get all router where operation_id is authorize
    router_authorize = [route for route in app.routes[4:] if "authorize" in str(route.operation_id).lower()]
    for route in router_authorize:
        method = list(route.methods)[0].lower()
        path = getattr(route, "path")
        openapi_schema["paths"][path][method]["security"] = [
            {
                "Bearer Auth": []
            }
        ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

@app.get('/')
async def home():
    return {
        'status_code': 200,
        'detail': 'Welcome to the Travel Mate API'
    }

# app.include_router(recipe_router)
# app.include_router(food_router)
# app.include_router(all_food_router)
# app.include_router(misc_router)
