_models = {}

def get_model(name:str):
    if name in _models:
        return _models[name]