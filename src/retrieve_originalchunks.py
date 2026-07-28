import psycopg2

DB_NAME = "SpeechDB"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = 5432


def get_originalchunks(video_name: str, chunk_numbers: list[int]):
    """
    Returns list of (number, originalchunks) for given video name
    and list of chunk numbers.
    """
    if not chunk_numbers:
        return []

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        cur = conn.cursor()

        placeholders = ", ".join(["%s"] * len(chunk_numbers))

        query = f"""
            SELECT oc.number, oc.originalchunks
            FROM overlapchunks AS oc
            JOIN videos AS v
              ON oc.videoid::integer = v.id
            WHERE v.name = %s
              AND oc.number::integer IN ({placeholders})
            ORDER BY oc.number::integer;
        """

        params = [video_name] + chunk_numbers

        cur.execute(query, params)
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    except Exception as e:
        print("Error while retrieving originalchunks:", e)
        return []


if __name__ == "__main__":
    video_name = input("Enter video name: ").strip()

    chunks_input = input(
        "Enter chunk numbers (comma separated): "
    ).strip()

    chunk_numbers = [
        int(x.strip()) for x in chunks_input.split(",") if x.strip()
    ]

    rows = get_originalchunks(video_name, chunk_numbers)

    if not rows:
        print(
            f"No originalchunks found for video '{video_name}' "
            f"and chunks {chunk_numbers}."
        )
    else:
        print(
            f"OriginalChunks for video '{video_name}' "
            f"and chunks {chunk_numbers}:"
        )
        for num, orig in rows:
            print(f"  chunk {num}: {orig}")
