import psycopg2

DB_NAME = "SpeechDB"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = 5432


def get_overlapchunks_by_video_name(video_name: str):
    conn = None
    cur = None

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
            SELECT oc.id,
                   oc.videoid,
                   oc.number,
                   oc.starttime,
                   oc.endtime,
                   oc.speaker,
                   oc.text,
                   oc.originalchunks
            FROM overlapchunks AS oc
            JOIN videos AS v
              ON oc.videoid::integer = v.id
            WHERE v.name = %s
            ORDER BY oc.number;
        """

        cur.execute(query, (str(video_name),))
        rows = cur.fetchall()

        chunks = []
        for row in rows:
            chunks.append({
                "id": row[0],
                "videoid": row[1],
                "number": row[2],
                "starttime": row[3],
                "endtime": row[4],
                "speaker": row[5],
                "text": row[6],
                "originalchunks": row[7],
            })

        return chunks

    except Exception as e:
        print("Error while retrieving overlapchunks:", e)
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    name = input("Enter video name: ").strip()   
    result = get_overlapchunks_by_video_name(name)

    print(f"\nFound {len(result)} chunks for video '{name}':\n")
    for ch in result[:5]: 
        print(f"Chunk {ch['number']}  [{ch['starttime']} -> {ch['endtime']}]")
        print(f"Speaker: {ch['speaker']}")
        print(ch['text'])
        print("-" * 60)
