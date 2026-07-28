import psycopg2

DB_NAME = "SpeechDB"
DB_USER = "postgres"
DB_PASSWORD = "1234" 
DB_HOST = "localhost"
DB_PORT = 5432


def get_embedchunks_for_video_and_model(model_name: str, video_name: str):
    """
    Retrieve all embed chunks for a given video and model.
    Returns a list of (chunk_number, embedding_vector).
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        cur = conn.cursor()

        query = """
            SELECT
                oc.number::integer AS chunk_number,
                ec.vector
            FROM embedchunks AS ec
            JOIN overlapchunks AS oc
              ON ec.overlapchunksid = oc.id
            JOIN videos AS v
              ON oc.videoid::integer = v.id
            WHERE ec.model = %s
              AND v.name   = %s
            ORDER BY oc.number::integer;
        """

        cur.execute(query, (model_name, video_name))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    except Exception as e:
        print("Error while retrieving embed chunks:", e)
        return []


if __name__ == "__main__":
    model_name = input("Enter model name: ").strip()
    video_name = input("Enter video name: ").strip()

    rows = get_embedchunks_for_video_and_model(model_name, video_name)

    if not rows:
        print(
            f"No embed chunks found for model '{model_name}' "
            f"and video '{video_name}'."
        )
    else:
        print(
            f"Found {len(rows)} embed chunks for model '{model_name}' "
            f"and video '{video_name}':"
        )
        for chunk_num, vec in rows:
            print(f"  chunk {chunk_num}: {vec}")
