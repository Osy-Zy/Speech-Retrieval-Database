import os
import json
import psycopg2


DB_NAME = "SpeechDB"
DB_USER = "postgres"
DB_PASSWORD = "1234"  
DB_HOST = "localhost"
DB_PORT = 5432

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_ROOT = os.path.join(BASE_DIR, "dataset")



def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def get_video_id(cur, video_name: str):
   
    cur.execute("SELECT id FROM videos WHERE name = %s LIMIT 1;", (video_name,))
    row = cur.fetchone()
    return row[0] if row else None


def overlap_row_exists(cur, video_id, number):
   
    cur.execute(
        "SELECT 1 FROM overlapchunks WHERE videoid = %s AND number = %s LIMIT 1;",
        (str(video_id), str(number)),
    )
    return cur.fetchone() is not None



def load_overlap_chunks(overlap_json_path: str):
    
    with open(overlap_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Expected top-level JSON object with 'chunk X' keys.")

    chunks = []

    for key, value in sorted(data.items(), key=lambda kv: int(''.join(ch for ch in kv[0] if ch.isdigit()) or 0)):
        if not isinstance(value, dict):
            continue

        num_str = ''.join(ch for ch in key if ch.isdigit())
        number = int(num_str) if num_str else None

        start = value.get("start")
        end = value.get("end")
        full_text = value.get("full_text")
        speaker = value.get("speaker")
        keys_list = value.get("keys", [])

        if isinstance(keys_list, list):
            original_str = ",".join(str(x) for x in keys_list)
        else:
            original_str = str(keys_list) if keys_list is not None else None

        chunks.append(
            {
                "number": number,
                "start": start,
                "end": end,
                "speaker": speaker,
                "text": full_text,
                "original_chunks": original_str,
            }
        )

    return chunks



def populate_overlapchunks_from_dataset():
    if not os.path.isdir(DATASET_ROOT):
        print(f" Dataset folder not found: {DATASET_ROOT}")
        return

    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    folders = sorted(os.listdir(DATASET_ROOT))

    for folder_name in folders:
        video_folder = os.path.join(DATASET_ROOT, folder_name)
        if not os.path.isdir(video_folder):
            continue

        print(f"\n Processing video folder (OverlapChunks): {folder_name}")

        video_id = get_video_id(cur, folder_name)
        if video_id is None:
            print(f"   No row in 'videos' for '{folder_name}', skipping.")
            continue

        overlap_folder = os.path.join(
            video_folder, "TranscriptionChunk_60Sec_Overlapping"
        )

        candidate_paths = [
            os.path.join(overlap_folder, "TranscriptionChunk_60Sec_Overlapping.json"),
            os.path.join(overlap_folder, "TranscriptionChunk_60Sec_Overlapping"),
        ]

        overlap_json_path = None
        for p in candidate_paths:
            if os.path.isfile(p):
                overlap_json_path = p
                break

        if overlap_json_path is None:
            print(f"    Overlap JSON not found in {overlap_folder}")
            continue

        chunks = load_overlap_chunks(overlap_json_path)
        print(f"   Found {len(chunks)} chunks.")

        insert_query = """
            INSERT INTO overlapchunks (
                videoid, number, starttime, endtime, speaker, text, originalchunks
            ) VALUES (%s,%s,%s,%s,%s,%s,%s);
        """

        for ch in chunks:
            number = ch["number"]

            if number is None:
                continue

            if overlap_row_exists(cur, video_id, number):
                continue

            cur.execute(
                insert_query,
                (
                    str(video_id),                      
                    str(number),                        
                    str(ch["start"]) if ch["start"] is not None else None,  
                    str(ch["end"]) if ch["end"] is not None else None,      
                    ch["speaker"],                        
                    ch["text"],                           
                    ch["original_chunks"],              
                ),
            )

        print(f"    Inserted chunks for video '{folder_name}'.")

    cur.close()
    conn.close()
    print("\n DONE: all OverlapChunks inserted into table 'overlapchunks'.")


if __name__ == "__main__":
    populate_overlapchunks_from_dataset()
