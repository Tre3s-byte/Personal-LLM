
def extract_last_user_message(messages):
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""

def route_request(messages):
    text = extract_last_user_message(messages)
    token_estimate = len(text)//4

    if token_estimate < 800:
        return{
            "task_type" : "general_chat",
            "model" : "medium",
            "needs_chunking" : False
        }
    if token_estimate < 1500:
        return{
            "task_type" : "light_summary",
            "model" : "medium",
            "needs_chunking" : False
        }
    return {
        "task_type": "heavy_summary",
        "model": "large",
        "needs_chunking": True,
    }