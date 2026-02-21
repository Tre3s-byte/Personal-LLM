from fastapi import APIRouter, Request, HTTPException
from services.inference import run_inference
from services.router import route_request
router = APIRouter()

#This function work on async in order to not to block the website workflow
#It will recieve the request, validate the content and call the model to generate the response



@router.post("/chat")
async def chat(request: Request):
    body = await request.json()

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

    if routing["needs_chunking"]:
        #Temporary fallback, chunking is not implemented yet
        response = run_inference(model_name = model_name, messages=messages)
    else:
        response = run_inference(model_name = model_name, messages=messages)

    return {"response": response}
