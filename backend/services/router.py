from config import ROUTER_LIGHT_THRESHOLD, ROUTER_HEAVY_THRESHOLD

def extract_last_user_message(messages):
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""

def route_request(messages):
    text = extract_last_user_message(messages)
    token_estimate = len(text)//4

    if token_estimate < ROUTER_LIGHT_THRESHOLD:
        return{
            "task_type" : "general_chat",
            "target_model" : "medium",
            "needs_chunking" : False
        }
    if token_estimate < ROUTER_HEAVY_THRESHOLD:
        return{
            "task_type" : "light_summary",
            "target_model" : "medium",
            "needs_chunking" : False
        }
    return {
        "task_type": "heavy_summary",
        "target_model": "large",
        "needs_chunking": True,
    }