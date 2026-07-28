import psycopg2

DB_NAME = "SpeechDB"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = 5432


def get_video_info_by_name(video_name: str):
    """
    Retrieve one video's information by its name.
    Returns a dict or None if not found.
    """
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
            SELECT id,
                   year,
                   name,
                   caption,
                   linktocaption,
                   linktovideo,
                   linktomp3,
                   linktotranscription,
                   linktext,
                   linksummary
            FROM videos
            WHERE name = %s
            LIMIT 1;
        """

        cur.execute(query, (str(video_name),))
        row = cur.fetchone()

        if row is None:
            return None

        video_info = {
            "id": row[0],
            "year": row[1],
            "name": row[2],
            "caption": row[3],
            "linktocaption": row[4],
            "linktovideo": row[5],
            "linktomp3": row[6],
            "linktotranscription": row[7],
            "linktext": row[8],
            "linksummary": row[9],
        }

        return video_info

    except Exception as e:
        print("Error while retrieving video info:", e)
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    name = input("Enter video name: ").strip()  
    info = get_video_info_by_name(name)

    if info is None:
        print(f"\nNo video found with name '{name}'.")
    else:
        print(f"\nInformation for video '{name}':\n")
        print(f"ID:               {info['id']}")
        print(f"Year:             {info['year']}")
        print(f"Caption:          {info['caption']}")
        print(f"Link to caption:  {info['linktocaption']}")
        print(f"Link to video:    {info['linktovideo']}")
        print(f"Link to mp3:      {info['linktomp3']}")
        print(f"Transcription:    {info['linktotranscription']}")
        print(f"Text link:        {info['linktext']}")
        print(f"Summary link:     {info['linksummary']}")
