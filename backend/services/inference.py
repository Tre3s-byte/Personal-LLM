from .loader import get_model
from .normalization import normalize_history_for_model

#This function calls the model previously loaded and generates the message
#normalize will structure the data inside the request according to the structure already decided

def generate(messages):
    llm = get_model()

    messages = normalize_history_for_model(messages)

    output = llm.create_chat_completion(
        messages=messages,
        max_tokens=1000,
        temperature=0.7,
        top_p=0.9,
    )
    print(output)

    return output["choices"][0]["message"]["content"].strip()
