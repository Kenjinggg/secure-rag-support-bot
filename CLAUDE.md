# Project context for Claude

## What this is
A portfolio RAG customer-support chatbot demo for Kenji's AI-integration freelance work (Fiverr/Upwork). Fictional store: Nusa Threads. The demo must answer ONLY from `data/`, cite sources, and refuse with the fixed fallback otherwise.

## Stack (keep it small, no LangChain/LlamaIndex in v1)
- Python 3.11+, Windows, venv in `.venv`
- Embeddings: sentence-transformers `all-MiniLM-L6-v2` (local, free)
- Vector store: Chroma, persisted in `chroma_db/` (gitignored)
- LLM: provider-agnostic wrapper in `rag/llm.py`; default Anthropic `claude-haiku-5-5`
- All settings in `rag/config.py`, overridable via `.env`

## Commands
- `python ingest.py`: rebuild the knowledge base (run after editing `data/`)
- `python ask.py --debug`: terminal chat with retrieval scores
- Test set: `tests/questions.md` (answer / refuse / prompt-injection cases)
- `python tests/run_questions.py [--debug] [--only 2,6]`: run the test set (~9 Haiku calls for all 13; use `--only` to save calls)
- `streamlit run app.py`: web chat UI (port 8501). Builds `chroma_db/` itself if missing.

## Rules
- Never read, print or commit `.env` or API keys.
- `.env.example` is committed and public: placeholders only, never a real key (it briefly held one on 2026-10-13 before the first push).
- Keep prompt-injection defenses intact (fenced context, tag stripping, relevance gate, fixed fallback). The security angle is the selling point; document any change in README "Security".
- Keep the code readable for clients: plain Python, short files, comments explaining why.
- Keep API spend low: Haiku by default, don't add calls in loops without asking.

## Design decisions (and why)
- Chunking splits at `##` headings first (`rag/chunking.py`). Mixed-topic chunks diluted scores: "Can I pay with GoPay?" scored 0.26 and was wrongly blocked by the 0.30 gate; it scores 0.42 with one topic per chunk. Docs in `data/` should keep one topic per `##` section.
- The prompt lets the bot answer when the docs settle a question without naming the exact item (complete list of shipping countries → "no Japan"). Otherwise Haiku refused Q2.
- The model ends answers with a `SOURCES:` line. `pipeline.py` strips it and keeps only names that were actually retrieved, so the bot can't cite a doc that doesn't exist.
- The prompt forbids "the context states…" wording. Haiku leaked it into customer answers.
- `app.py` caps questions per session and per day (`MAX_QUESTIONS_PER_SESSION` / `MAX_QUESTIONS_PER_DAY` in config), checked before any model call. Public link = strangers spend Kenji's API budget. The daily counter is in-process memory, so it resets when the server restarts.
- `app.py` imports torch/chromadb inside `load_rag()`, not at the top: a cold import takes ~15 s and would show visitors a blank page.
- `requirements.txt` uses the CPU-only PyTorch index so Linux hosts don't download ~2.5 GB of CUDA libraries.

## Status (2026-10-13)
- v1 done: all 13 test questions pass. Q9 (student discount) varies between "we don't offer one" and the fallback; both are acceptable since no code is invented.
- Watch item: with smaller chunks, injection questions score closer to the gate (Q12 at 0.20 vs MIN_SCORE 0.30). Rerun 10–13 after any change to chunking, data or `MIN_SCORE`.
- Repo: https://github.com/Kenjinggg/secure-rag-support-bot (branch `main`). Before every push, check that no API key is in tracked files.
- Kenji is learning RAG through this project: show how to check results yourself (scores, `--debug`, the runner), not just verdicts.

## Roadmap
- v1: terminal pipeline passes all 13 test questions ✅
- v1.1: Streamlit UI + deploy for a public link on Streamlit Community Cloud. Live since 2026-10-14; only the README demo GIF is left (see Deployment).
- v2: embeddable widget for a Shopify store

## Deployment (decided 2026-10-14)
Host: **Streamlit Community Cloud**, deployed from the GitHub repo, `app.py` as entry point.

Why not the others (checked 2026-10-14):
- Hugging Face Spaces: its docs now say Gradio/Docker Spaces need a paid plan (PRO) on personal accounts, and Streamlit isn't listed as an SDK option any more. Not free for this app.
- Render / Railway / Fly.io / Koyeb free tiers: trial credits or ~512 MB RAM; torch + MiniLM likely runs out of memory.
- Cloud Run / a VPS: fine, but overkill for a demo. Keep them in mind for paid client deployments, where the app must not sleep.

Streamlit Cloud facts that affect the code:
- Memory limit ~2.7 GB (fine for MiniLM + CPU torch).
- The app sleeps after 12 h without traffic. Waking restarts the process, and the filesystem is not persistent across restarts.
- Chroma may need the old-SQLite fix (`pysqlite3-binary` + swapping it in for `sqlite3` before chromadb is imported). Apply it only if the deploy actually fails on SQLite, and keep it guarded so local Windows runs are unaffected.
- `chroma_db/` is gitignored, so the deployed app must build it on first start (`app.py` already does this; confirm it works there).

Tasks for Claude Code:
- [x] Deploy to Streamlit Community Cloud (live 2026-10-14: https://nusa-threads-support.streamlit.app/). No SQLite fix was needed; the index builds on first start there. Kenji pastes the key into the app's Secrets himself; never ask him to paste it into chat or a file in the repo.
- [x] Make config read the key from Streamlit Secrets as well as `.env` (st.secrets / environment variable), without breaking local runs. Done in `app.py` (`load_streamlit_secrets()`, before config is imported); `.streamlit/secrets.toml` is gitignored.
- [x] **Daily cap weakness:** the `MAX_QUESTIONS_PER_DAY` counter is in-process memory, so it resets every time the app wakes from sleep or restarts. Treat it as a speed bump, not a limit. Don't build persistent storage for this demo. Instead: keep the per-session cap, add a short note in README "Security" explaining the hard limit is the provider spend cap, and remind Kenji to set it.
- [x] After deploy, run the 13 test questions against the live app (at least Q1, Q6, Q8, Q11–13) and report results. Q1, Q6, Q8, Q11, Q12, Q13 all passed live on 2026-10-14.
- [x] Add the live link and a "may take ~1 minute to wake up" note at the top of README.
- [ ] Add a short demo GIF/video to the top of README (Kenji records it: one normal answer with sources, one refusal, one blocked injection). Clients watch the video more often than they click the link, so it matters more than the link.

Kenji's manual steps (remind him, don't do them):
- Create a **separate API key** just for the deployed app (not his laptop key), and set a **monthly spend limit (~$5)** in the Claude Console. That limit is the real protection against strangers using the public link.
- Before sending a proposal, open the live link so the app is awake when the client clicks.
