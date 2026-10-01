from python_review_bot.rag import ingest_directory

if __name__ == "__main__":
    n = ingest_directory()
    print(f"Ingested {n} chunks.")
