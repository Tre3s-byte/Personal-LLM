from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from .inference import generate

router = APIRouter()


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]


@router.post("/chat")
def chat(request: ChatRequest):
    response = generate(request.messages)
    return {"response": response}
