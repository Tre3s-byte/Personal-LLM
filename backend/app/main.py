from fastapi import FastAPI
from .routes import router
from .loader import get_model

app = FastAPI(title="Local LLM API")

app.include_router(router)


@app.on_event("startup")
def load_model():
    get_model()
