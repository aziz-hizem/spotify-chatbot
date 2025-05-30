from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .llm_handler import process_user_input
from .spotify_api import ensure_token_validity
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_input = body.get("message")
    logging.info(f"Received user input: {user_input}")
    ensure_token_validity()  # refresh if needed
    response = process_user_input(user_input)
    logging.info(f"Response to user: {response}")
    return {"response": response}