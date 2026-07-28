import os
import psycopg2
import numpy as np


DB_NAME = "SpeechDB"
DB_USER = "postgres"
DB_PASSWORD = "1234"  
DB_HOST = "localhost"
DB_PORT = 5432

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_ROOT = os.path.join(BASE_DIR, "dataset")

MODEL_FILES = {
    "jinaV3": "jinaV3_embedding.npy",
    "omarelshehy": "omarelshehy_embedding.npy",
    "qwen3-0.6B": "Qwen3-0.6B_embedding.npy",
}



def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def ensure_pgvector_and_table():
  
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS embedchunks (
            id SERIAL PRIMARY KEY,
            overlapchunksid INTEGER REFERENCES overlapchunks(id),
            model TEXT,
            vector vector
        );
        """
    )

    cur.close()
    conn.close()


def get_video_id(cur, video_name: str):
    
    cur.execute("SELECT id FROM videos WHERE name = %s LIMIT 1;", (video_name,))
    row = cur.fetchone()
    return row[0] if row else None


def get_overlapchunk_id(cur, video_id, number):
    
    cur.execute(
        """
        SELECT id
        FROM overlapchunks
        WHERE videoid = %s AND number = %s
        LIMIT 1;
        """,
        (str(video_id), str(number)),
    )
    row = cur.fetchone()
    return row[0] if row else None


def embed_row_exists(cur, overlapchunksid, model):
   
    cur.execute(
        """
        SELECT 1
        FROM embedchunks
        WHERE overlapchunksid = %s AND model = %s
        LIMIT 1;
        """,
        (overlapchunksid, model),
    )
    return cur.fetchone() is not None


def vector_to_pgvector(v):
    v = v.astype(float).tolist()
    return "[" + ",".join(str(x) for x in v) + "]"



def populate_embedchunks_from_dataset():
    ensure_pgvector_and_table()

    if not os.path.isdir(DATASET_ROOT):
        print(f"Dataset folder not found: {DATASET_ROOT}")
        return

    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    folders = sorted(os.listdir(DATASET_ROOT))

    for folder_name in folders:
        video_folder = os.path.join(DATASET_ROOT, folder_name)
        if not os.path.isdir(video_folder):
            continue

        print(f"\n Processing video folder (Embeddings): {folder_name}")

        video_id = get_video_id(cur, folder_name)
        if video_id is None:
            print(f" No row in 'videos' for '{folder_name}', skipping.")
            continue

        overlap_folder = os.path.join(
            video_folder, "TranscriptionChunk_60Sec_Overlapping"
        )

        for model_name, fname in MODEL_FILES.items():
            npy_path = os.path.join(overlap_folder, fname)

            if not os.path.isfile(npy_path):
                print(f"  Embedding file not found for model '{model_name}': {npy_path}")
                continue

            print(f"  Loading embeddings for model '{model_name}'...")
            embeddings = np.load(npy_path)

            if embeddings.ndim != 2:
                print(f"   Unexpected shape {embeddings.shape} for {npy_path}, skipping.")
                continue

            num_chunks, dim = embeddings.shape
            print(f"   Shape: {num_chunks} chunks × {dim} dims")

            inserted_count = 0
            for idx in range(num_chunks):
                chunk_number = idx + 1  

                overlap_id = get_overlapchunk_id(cur, video_id, chunk_number)
                if overlap_id is None:
                    continue

                if embed_row_exists(cur, overlap_id, model_name):
                    continue

                vec_str = vector_to_pgvector(embeddings[idx])

                cur.execute(
                    """
                    INSERT INTO embedchunks (overlapchunksid, model, vector)
                    VALUES (%s, %s, %s::vector);
                    """,
                    (overlap_id, model_name, vec_str),
                )
                inserted_count += 1

            print(f"  Inserted {inserted_count} rows for model '{model_name}'.")

    cur.close()
    conn.close()
    print("\n DONE: all embeddings inserted into table 'embedchunks'.")


if __name__ == "__main__":
    populate_embedchunks_from_dataset()
