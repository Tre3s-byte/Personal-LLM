from .loader import get_model
from .normalization import normalize_history_for_model


def generate(messages):
    llm = get_model()

    messages = normalize_history_for_model(messages)

    output = llm.create_chat_completion(
        messages=messages,
        max_tokens=1000,
        temperature=0.7,
        top_p=0.9,
    )

    return output["choices"][0]["message"]["content"].strip()
