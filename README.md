# RAG Customer Support Demo

A customer-support chatbot that answers **only** from a store's own help docs, cites its sources, and says "I don't know" instead of making things up. Built for **Nusa Threads**, a fictional online clothing store.

## How it works

1. **Ingest:** the help docs in `data/` are split into chunks, embedded with a free local model (`all-MiniLM-L6-v2`), and stored in a local Chroma vector database.
2. **Retrieve:** each question is embedded, and the most similar chunks are fetched.
3. **Answer:** the chunks are sent to the LLM with strict rules: answer only from this context, otherwise fall back to a fixed message.

No frameworks (LangChain etc.). The whole pipeline is about 200 lines of plain Python.

## Security: prompt-injection hardening

- **Fenced untrusted input.** Docs and questions are wrapped in `<context>` / `<question>` tags, and the system prompt treats everything inside them as data, never as instructions.
- **Tag stripping.** Any fence tags found in the input are removed, so a malicious question or document can't "close" the fence and inject fake system instructions.
- **Relevance gate.** If no doc chunk is relevant enough, the bot refuses *without calling the LLM*. Off-topic and injection attempts often never reach the model.
- **Fixed fallback.** Refusals use one exact message, so the bot can't be talked into inventing discount codes, policies or contact details. The one exception: if the docs settle a question without naming the exact item (e.g. a complete list of shipping countries answers "Do you ship to Japan?" with no), the bot answers from the docs instead of refusing.
- **Validated citations.** The model names the docs it used, and only names that were actually retrieved are shown, so it can't cite a source that doesn't exist.
- **One topic per chunk.** Docs are split at `##` headings, so each chunk scores cleanly against the relevance gate instead of being diluted by unrelated topics.
- **Input length cap.** Questions are truncated to 1,000 characters.
- **Usage limits (web app).** A public link means anyone can spend the API budget, so the app caps questions per visitor session (`MAX_QUESTIONS_PER_SESSION`, default 15) and per day across all visitors (`MAX_QUESTIONS_PER_DAY`, default 300), checked before any model call. These are speed bumps, not hard limits: the daily counter lives in memory and resets whenever the app restarts or wakes from sleep, and a visitor can start a new session by reloading. **The hard limit is the provider's spend cap:** give the deployed app its own API key with a monthly spend limit (e.g. $5) in the Anthropic Console.

## Setup (Windows)

```powershell
cd C:\Kenji-Work\rag-demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and paste your Anthropic API key. Then:

```powershell
python ingest.py      # build the knowledge base (re-run after editing data/)
python ask.py         # chat in the terminal
python ask.py --debug # also show retrieved chunks and their scores
```

The first run downloads the embedding model (~90 MB).

## Web app

```powershell
streamlit run app.py
```

A chat page with clickable example questions (including injection attempts) and a "Show retrieval details" panel per answer, which shows the retrieved chunks, their scores and whether the relevance gate let the question through. If `chroma_db/` doesn't exist yet, the app builds it on first start, so a fresh deploy needs no manual `ingest.py` step.

## Switching LLM provider

Edit `.env`. No code changes needed:

```
LLM_PROVIDER=openai
LLM_MODEL=<model name>
OPENAI_API_KEY=...
```

## Testing

`tests/questions.md` lists 13 questions: ones the bot should answer, ones it should refuse, and prompt-injection attempts it should resist. Run them all with:

```powershell
python tests/run_questions.py              # all 13
python tests/run_questions.py --debug      # also show retrieved chunks and scores
python tests/run_questions.py --only 2,6   # selected questions only
```

## Using your own docs

Replace the files in `data/` with any `.md` or `.txt` files, set `STORE_NAME` and `SUPPORT_EMAIL` in `.env`, and run `python ingest.py`.
