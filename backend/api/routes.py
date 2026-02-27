from fastapi import APIRouter, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from services.inference import run_routed_inference
from services.router import route_request
from utils.logging import (
    log_inference_completed,
    log_inference_started,
    log_inference_telemetry,
)
import json
import logging
import time

router = APIRouter()

#This function work on async in order to not to block the website workflow
#It will recieve the request, validate the content and call the model to generate the response

logger = logging.getLogger(__name__)

@router.post("/chat")
async def chat(request: Request):
    logger.info("Received /chat request")
    raw = await request.body()
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON payload", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
   
    #Message validation (not empty)
    if "messages" not in body:
        raise HTTPException(status_code=400, detail="Missing 'messages' in request body")
    
    messages = body["messages"]
    
    #Type validation (Not a list)
    if not isinstance(messages, list):
        return {"error" : "'messages' must be a list"}
    
    #Type verification (It is a Dict)
    for msg in messages:
        if not isinstance(msg, dict):
            return {"error" : "Each 'message' must be a dict"}
        
        if "role" not in msg or "content" not in msg:
            return {"error" : "Each 'message' must contain 'role' and 'content'"}
        
        if not isinstance(msg["role"], str) or not isinstance(msg["content"], str):
            return {"error" : "'role' and 'content' must be strings"}
    
    routing = route_request(messages)
    model_name = routing["target_model"]

    start = time.perf_counter()
    log_inference_started(model_name=model_name, strategy=routing.get("chunk_strategy"))

    response = await run_in_threadpool(
        run_routed_inference,
        model_name=model_name,
        messages=messages,
        routing=routing,
    )

    latency = time.perf_counter() - start
    usage = response.get("usage", {}) if isinstance(response, dict) else {}

    log_inference_telemetry(
        model=model_name,
        task_type=routing.get("task_type"),
        strategy=routing.get("chunk_strategy"),
        latency_seconds=latency,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
        models_used=response.get("models_used", [model_name]),
        chunk_info=response.get("chunk_info"),
    )
    log_inference_completed(model_name=model_name, latency_seconds=latency)

    logger.info("Generated response successfully")

    return {"response": response.get("text", "")}
