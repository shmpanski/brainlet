import os

from fastapi import FastAPI
from weaviate import Client

from brainlet.core import ask_question, Answer

WEAVIATE_CLIENT_URL = os.getenv("WEAVIATE_CLIENT_URL", "http://127.0.0.1:8080")

app = FastAPI()
client = Client(WEAVIATE_CLIENT_URL)


@app.get("/", response_model_exclude_none=True)
async def ask(question: str) -> Answer:
    return ask_question(client, question)
