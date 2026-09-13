"""CLI: (re)build the retrieval index from app/rag/corpus.py.

Usage: python -m app.rag.build_index
"""

from app.rag.store import get_store


def main() -> None:
    store = get_store()
    n = store.build_index()
    print(f"Index rebuilt with {n} chunks.")
    print(f"Sanity check: {store.retrieve('what should I wear in the lab?', top_k=2)}")


if __name__ == "__main__":
    main()
