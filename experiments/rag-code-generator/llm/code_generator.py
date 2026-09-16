# spotify_chatbot/llm/code_generator.py
import os
from dotenv import load_dotenv
from jinja2 import Template
from llm.vectorstore import query_relevant_docs
import requests  # for Groq call if needed

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Set this in your .env


def load_prompt_template():
    with open("llm/prompts/generate_code.txt", "r", encoding="utf-8") as f:
        return Template(f.read())

def generate_code_from_query(query: str) -> str:
    relevant_docs = query_relevant_docs(query, n_results=5)
    template = load_prompt_template()
    prompt = template.render(docs="\n".join(relevant_docs), query=query)

    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
    )
    return response.json()["choices"][0]["message"]["content"].strip()
