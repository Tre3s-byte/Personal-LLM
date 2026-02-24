from utils.normalization import normalize_history_for_model
from model.registry import get_model
from config import MODEL_CONFIG
import logging
import time


logger = logging.getLogger(__name__)

#This function calls the model previously loaded and generates the message
#normalize will structure the data inside the request according to the structure already decided

def run_inference(model_name:str, messages:list):

    if model_name not in MODEL_CONFIG:
        raise ValueError(f'Unknown model: {model_name}')
    
    cfg = MODEL_CONFIG[model_name]

    logger.info(f'Starting inference for model: {model_name}')
    start_time = time.time()
    
    model = get_model(model_name)
    messages = normalize_history_for_model(messages)

    output = model.create_chat_completion(
        messages = messages,
        max_tokens=cfg['max_tokens'],
        temperature=cfg['temperature'],
        top_p = cfg['top_p']
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    response = output['choices'][0]['message']['content'].strip()
    generated_tokens = output['usage']['completion_tokens']
    tps = generated_tokens / processing_time
    
    logger.info(f'Inference completed for model: {model_name}, processing time: {processing_time:.2f} seconds, tokens generated: {generated_tokens}, tokens per second: {tps:.2f}')
    
    return response
