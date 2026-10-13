"""Run every question in tests/questions.md through the real pipeline.

    python tests/run_questions.py              # all 13 questions
    python tests/run_questions.py --debug      # also show retrieved chunks + scores
    python tests/run_questions.py --only 2,6   # just some questions (saves API calls)

For each question it prints what we expected, what the bot said, and a
quick check of the behaviour (answered vs refused). Whether an answer is
*correct* is up to you: read it against the expected note.
"""
import re
import sys
from pathlib import Path

# Make "from rag import ..." work when run from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag import config  # noqa: E402
from rag.pipeline import FALLBACK, RAG  # noqa: E402

QUESTIONS_FILE = Path(__file__).with_name("questions.md")


def load_questions() -> list[dict]:
    """Parse questions.md: '## Should ...' headers set the expected behaviour."""
    questions, expect = [], None
    for line in QUESTIONS_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            expect = "answer" if "answer" in line.lower() else "refuse"
            continue
        m = re.match(r"\s*(\d+)\.\s+(.*?)(?:\s{2,}->\s*(.*))?$", line)
        if m:
            questions.append({"n": int(m.group(1)), "q": m.group(2).strip(),
                              "note": (m.group(3) or "").strip(), "expect": expect})
    return questions


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console + "–" characters
    debug = "--debug" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}

    questions = [q for q in load_questions() if only is None or q["n"] in only]
    print(f"Loading... (gate MIN_SCORE={config.MIN_SCORE}, TOP_K={config.TOP_K})\n")
    rag = RAG()

    matched = 0
    for item in questions:
        result = rag.answer(item["q"])
        got = "refuse" if result["answer"] == FALLBACK else "answer"
        ok = got == item["expect"]
        matched += ok
        top = result["chunks"][0]["score"] if result["chunks"] else 0.0
        gate = "passed" if top >= config.MIN_SCORE else "BLOCKED (no API call)"

        print(f"--- Q{item['n']}: {item['q']}")
        print(f"Expected: {item['expect']}" + (f"  ({item['note']})" if item["note"] else ""))
        print(f"Got:      {got}  {'OK' if ok else '<-- CHECK'}   top score {top:.2f}, gate {gate}")
        print(f"Bot:      {result['answer']}")
        print(f"Sources:  {', '.join(result['sources']) or '-'}")
        if debug:
            for c in result["chunks"]:
                preview = c["text"][:70].replace("\n", " ")
                print(f"   {c['score']:.2f}  {c['source']:<12} {preview}...")
        print()

    print(f"Behaviour matched on {matched}/{len(questions)}. "
          "Now read each answer against its expected note.")


if __name__ == "__main__":
    main()
