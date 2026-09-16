# Experiment: RAG Code Generator for the Spotify API

> **Status: unfinished experiment.** Kept to document the approach; it is not wired to the chat app.

The chatbot in this repository only supports actions that are coded by hand. This experiment explored a more general approach with **retrieval-augmented generation (RAG)**: instead of predefined actions, retrieve the relevant parts of the Spotify Web API documentation and let an LLM write the Python code for any request.

## Pipeline

```
Spotify Web API reference ──scraper.py──► data/endpoints.json
                                              │
                                          embed.py (all-MiniLM-L6-v2 embeddings)
                                              ▼
                                        ChromaDB vector store
                                              │  top 5 similar docs
user request ──► llm/code_generator.py ◄──────┘
                        │  prompt template (Jinja2) + Groq (Llama 3.3 70B)
                        ▼
                 generated Python code
```

| File | Role |
|---|---|
| `scraper.py` | Crawls the API reference with Playwright and BeautifulSoup and saves each endpoint (title, URL, method, path, description, scopes, parameters) |
| `embed.py` | Turns each endpoint into a text chunk, embeds it with Sentence Transformers and stores it in a persistent ChromaDB collection |
| `llm/vectorstore.py` | Retrieves the chunks most similar to a request |
| `llm/code_generator.py` | Renders the prompt with the retrieved docs and asks the LLM for the code |
| `llm/test.py` | Example request: *"Add 'Somebody That I Used to Know' to my June playlist"* |

## Where it stopped

- **Scraping**: only endpoint titles and URLs were captured; the selectors did not pick up the method, path, parameters or scopes, so the knowledge base is too thin for reliable code generation.
- **Two vector stores**: `embed.py` writes to a persistent ChromaDB collection in `data/chroma/`, while `llm/vectorstore.py` builds its own in-memory collection from `data/chunks.json`. They were never unified.
- **No interface**: requests are run from `llm/test.py`, and the generated code is printed, not executed.

## Running it

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # add your Groq API key

python scraper.py
python embed.py
python -m llm.test
```
