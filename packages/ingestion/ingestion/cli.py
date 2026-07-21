import argparse
import os
import yaml
from datetime import datetime
from ingestion.loaders.local import load_document
from ingestion.chunking.text_splitter import chunk_text
from ingestion.embeddings.ollama import OllamaEmbedder
from ingestion.vector_store.qdrant import QdrantStore


def main():
    parser = argparse.ArgumentParser(description="Ingest documents for a university.")
    parser.add_argument(
        "--university", type=str, required=True, help="Slug of the university to ingest"
    )
    args = parser.parse_args()
    slug = args.university

    # Paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    uni_dir = os.path.join(base_dir, "universities", slug)
    config_path = os.path.join(uni_dir, "config.yaml")
    sources_dir = os.path.join(uni_dir, "sources")

    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    collection_name = config.get("qdrant_collection", f"{slug}_collection")

    # Initialize components
    print("Initializing components...")
    embedder = OllamaEmbedder()
    embedder.ensure_model_pulled()

    vector_store = QdrantStore(collection_name=collection_name, vector_size=768)

    # Clear existing data for this university
    vector_store.delete_university_data(slug)

    if not os.path.exists(sources_dir):
        print(f"No sources directory found at {sources_dir}")
        return

    files_processed = 0
    total_chunks = 0
    total_vectors = 0

    print(f"\nStarting ingestion for {slug}...")
    for filename in os.listdir(sources_dir):
        filepath = os.path.join(sources_dir, filename)
        if not os.path.isfile(filepath):
            continue

        print(f"Processing: {filename}")

        try:
            # 1. Load
            text = load_document(filepath)
            if not text.strip():
                print(f"  Warning: Empty text extracted from {filename}")
                continue

            # 2. Chunk
            chunks = chunk_text(text, chunk_size=500, overlap=50)
            if not chunks:
                print(f"  Warning: No chunks generated for {filename}")
                continue
            print(f"  Created {len(chunks)} chunks.")

            # 3. Embed
            embeddings = embedder.embed_documents(chunks)

            # 4. Prepare payloads and Upsert
            payloads = [
                {
                    "source_url_or_filename": filename,
                    "university_slug": slug,
                    "chunk_text": chunk,
                    "ingested_at": datetime.utcnow().isoformat(),
                }
                for chunk in chunks
            ]

            vector_store.upsert_points(embeddings, payloads)

            files_processed += 1
            total_chunks += len(chunks)
            total_vectors += len(embeddings)
            print(f"  Upserted {len(embeddings)} vectors.")

        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    print("\n=== Ingestion Summary ===")
    print(f"University:      {slug}")
    print(f"Files processed: {files_processed}")
    print(f"Chunks created:  {total_chunks}")
    print(f"Vectors upserted:{total_vectors}")
    print("=========================\n")


if __name__ == "__main__":
    main()
