from fastapi import FastAPI
from app.routes import router as app_router
from api.routes import router as api_router



app = FastAPI(title="Local LLM API")

app.include_router(app_router)
app.include_router(api_router)