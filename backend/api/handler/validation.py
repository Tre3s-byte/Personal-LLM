import json
from fastapi import Request, HTTPException


async def parse_request_body(request: Request) -> dict:
    raw = await request.body()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")


def validate_messages(body: dict) -> list:
    if "messages" not in body:
        raise HTTPException(
            status_code=400, detail="Missing 'messages' in request body"
        )
    messages = body["messages"]
    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="'messages' must be a list")
    for msg in messages:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            raise HTTPException(
                status_code=400, detail="Each message must contain role and content"
            )
    return messages
