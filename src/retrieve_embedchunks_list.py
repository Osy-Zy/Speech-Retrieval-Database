import psycopg2

DB_NAME = "SpeechDB"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = 5432


def get_embedchunks_for_chunks(video_name, model_name, chunk_numbers):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        query = """
            SELECT oc.number, ec.vector
            FROM embedchunks ec
            JOIN overlapchunks oc ON ec.overlapchunksid = oc.id
            JOIN videos v ON oc.videoid::integer = v.id
            WHERE v.name = %s
              AND ec.model = %s
              AND oc.number::integer = ANY(%s)
            ORDER BY oc.number::integer;
        """


        cur.execute(query, (video_name, model_name, chunk_numbers))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    except Exception as e:
        print("Error while retrieving embeddings:", e)
        return []


if __name__ == "__main__":
    video_name = input("Enter video name: ").strip()
    model_name = input("Enter model name: ").strip()
    chunks_str = input("Enter chunk numbers (comma separated): ")

    chunk_numbers = [int(x.strip()) for x in chunks_str.split(",") if x.strip().isdigit()]

    rows = get_embedchunks_for_chunks(video_name, model_name, chunk_numbers)

    if not rows:
        print("\n No embeddings found for these inputs.\n")
    else:
        print(f"\n Embeddings for video '{video_name}', model '{model_name}':\n")
        for chunk_num, vector in rows:
            print("====================================")
            print(f" Chunk Number: {chunk_num}")
            print(f" Embed Chunks:\n{vector}\n")
