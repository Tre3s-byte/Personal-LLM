import os
import json
from uuid import uuid4

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHATS_DIR = os.path.join(BASE_DIR, "chats")
os.makedirs(CHATS_DIR, exist_ok=True)

conversations = {}


def list_chats():
    return [f.replace(".json", "") for f in os.listdir(CHATS_DIR)]


def load_chat(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            conversations[chat_id] = json.load(f)
    else:
        conversations[chat_id] = []

    return conversations[chat_id]


def save_chat(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(conversations[chat_id], f, indent=2, ensure_ascii=False)


def create_new_chat():
    chat_id = f"chat-{uuid4().hex[:6]}"
    conversations[chat_id] = []
    save_chat(chat_id)
    return chat_id, []
