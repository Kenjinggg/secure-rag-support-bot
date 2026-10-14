"""Run test questions through the real pipeline.

    python tests/run_questions.py                       # the 13 core questions
    python tests/run_questions.py --file tests/extended_questions.md
    python tests/run_questions.py --debug               # also show retrieved chunks + scores
    python tests/run_questions.py --only 2,6            # just some questions (saves API calls)
    python tests/run_questions.py --retrieval-only      # check retrieval only: no API calls, free

For each question it prints what we expected and what the bot did, with
automatic checks for:
  - behaviour: answered vs refused (section headers in the file say which)
  - source: the doc named in brackets, e.g. (faq.md), was retrieved
  - leaks: the reply mentions "context" or its own instructions
Whether an answer is *correct* is still up to you: read it against the note.
"""
import re
import sys
from pathlib import Path

# Make "from rag import ..." work when run from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag import config  # noqa: E402
from rag.pipeline import FALLBACK, RAG  # noqa: E402

DEFAULT_FILE = Path(__file__).with_name("questions.md")

# Words a customer-facing reply should never contain.
LEAK_WORDS = re.compile(
    r"\bcontext\b|\barticles?\b|\bexcerpts?\b|information provided|help docs (say|state)|"
    r"<\s*/?\s*(doc|question|store_policies|policy|customer_question)|system prompt|my instructions",
    re.IGNORECASE,
)


def load_questions(path: Path) -> list[dict]:
    """Parse a questions file: '## ...' headers set the expected behaviour."""
    questions, expect = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            header = line.lower()
            if "either" in header:
                expect = "either"
            elif "should answer" in header:
                expect = "answer"
            else:
                expect = "refuse"
            continue
        m = re.match(r"\s*(\d+)\.\s+(.*?)(?:\s{2,}->\s*(.*))?$", line)
        if m:
            note = (m.group(3) or "").strip()
            source = re.search(r"\(([\w-]+\.md)\)\s*$", note)
            questions.append({"n": int(m.group(1)), "q": m.group(2).strip(), "note": note,
                              "expect": expect, "source": source.group(1) if source else None})
    return sorted(questions, key=lambda q: q["n"])


def arg(name: str):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console + "–" characters
    debug = "--debug" in sys.argv
    retrieval_only = "--retrieval-only" in sys.argv
    path = Path(arg("--file") or DEFAULT_FILE)
    only = {int(x) for x in arg("--only").split(",")} if arg("--only") else None

    questions = [q for q in load_questions(path) if only is None or q["n"] in only]
    print(f"Loading... {path.name}: {len(questions)} questions "
          f"(gate MIN_SCORE={config.MIN_SCORE}, TOP_K={config.TOP_K})\n")
    rag = RAG()

    problems = []
    for item in questions:
        if retrieval_only:
            chunks = rag.retrieve(item["q"])
            answer, sources = None, []
        else:
            result = rag.answer(item["q"])
            chunks, answer, sources = result["chunks"], result["answer"], result["sources"]

        top = chunks[0]["score"] if chunks else 0.0
        gate_ok = top >= config.MIN_SCORE
        retrieved = [c["source"] for c in chunks]
        issues = []

        # Retrieval checks (free): the right doc must be found and pass the gate.
        if item["expect"] == "answer":
            if not gate_ok:
                issues.append(f"gate blocked it ({top:.2f} < {config.MIN_SCORE})")
            if item["source"] and item["source"] not in retrieved:
                issues.append(f"{item['source']} not retrieved")
            elif item["source"] and retrieved[0] != item["source"]:
                issues.append(f"{item['source']} retrieved but not first")  # warning only

        # Answer checks (need the model).
        if answer is not None:
            got = "refuse" if answer == FALLBACK else "answer"
            if item["expect"] in ("answer", "refuse") and got != item["expect"]:
                issues.append(f"expected {item['expect']}, got {got}")
            if LEAK_WORDS.search(answer):
                issues.append("reply leaks prompt wording")
            if item["source"] and got == "answer" and item["source"] not in sources:
                issues.append(f"cited {sources}, expected {item['source']}")

        hard = [i for i in issues if "not first" not in i]
        if hard:
            problems.append(item["n"])
        status = "CHECK: " + "; ".join(issues) if issues else "OK"
        if issues and not hard:
            status = "OK (warning: " + "; ".join(issues) + ")"

        print(f"--- Q{item['n']}: {item['q']}")
        print(f"Expected: {item['expect']}" + (f"  ({item['note']})" if item["note"] else ""))
        print(f"Result:   {status}   top {top:.2f} {retrieved[0] if retrieved else '-'}")
        if answer is not None:
            print(f"Bot:      {answer}")
            print(f"Sources:  {', '.join(sources) or '-'}")
        if debug:
            for c in chunks:
                preview = c["text"][:70].replace("\n", " ")
                print(f"   {c['score']:.2f}  {c['source']:<12} {preview}...")
        print()

    passed = len(questions) - len(problems)
    print(f"Automatic checks passed: {passed}/{len(questions)}"
          + (f"   CHECK: {', '.join(f'Q{n}' for n in problems)}" if problems else ""))
    if not retrieval_only:
        print("Now read each answer against its expected note.")


if __name__ == "__main__":
    main()
