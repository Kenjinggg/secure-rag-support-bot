"""Chat with the knowledge base in your terminal.

    python ask.py            # interactive
    python ask.py --debug    # also show retrieved chunks and scores
"""
import sys

from rag.pipeline import RAG


def main():
    debug = "--debug" in sys.argv
    print("Loading... (first run downloads the embedding model)")
    rag = RAG()
    print("Ready. Ask a question, or type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        result = rag.answer(question)
        print(f"\nBot: {result['answer']}")
        if result["sources"]:
            print(f"Sources: {', '.join(result['sources'])}")
        if debug:
            print("\n[retrieved]")
            for c in result["chunks"]:
                preview = c["text"][:80].replace("\n", " ")
                print(f"  {c['score']:.2f}  {c['source']}  {preview}...")
        print()


if __name__ == "__main__":
    main()
