from models.sbert_model import model

def generate_embedding(text):
    embedding = model.encode(text)
    return embedding.tolist()