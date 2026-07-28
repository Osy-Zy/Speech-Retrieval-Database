import os
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



def safe_read_text_file(path):

    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None


def find_file_starting_with(folder, prefix):
   
    if not os.path.isdir(folder):
        return None

    for fname in os.listdir(folder):
        if fname.startswith(prefix):
            return os.path.join(folder, fname)
    return None


def video_row_exists(cur, name):
    
    cur.execute('SELECT 1 FROM "videos" WHERE name = %s LIMIT 1;', (name,))
    return cur.fetchone() is not None



def populate_videos_from_dataset():
    
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

        print(f"\n Processing video folder: {folder_name}")

        year = folder_name[:4]

        caption_path = os.path.join(video_folder, "caption.txt")
        caption_text = safe_read_text_file(caption_path)

        transcription_folder = os.path.join(video_folder, "Transcription")

        full_text_path = find_file_starting_with(
            transcription_folder, "transcription_full_text"
        )

        whisper_json_path = find_file_starting_with(
            transcription_folder, "transcription_whisper_large_v3"
        )
        summary_path = find_file_starting_with(
            transcription_folder, "summary"
        )
        link_to_caption = (
            os.path.abspath(caption_path) if os.path.isfile(caption_path) else None
        )
        link_text = os.path.abspath(full_text_path) if full_text_path else None
        link_transcription = (
            os.path.abspath(whisper_json_path) if whisper_json_path else None
        )
        link_summary = os.path.abspath(summary_path) if summary_path else None

        if video_row_exists(cur, folder_name):
            print(f"   Video '{folder_name}' already exists, skipping.")
            continue

        insert_query = '''
            INSERT INTO "videos" (
                year, name, caption, linktocaption,
                linktovideo, linktomp3, linktotranscription,
                linktext, linksummary
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
        '''

        cur.execute(
            insert_query,
            (
                year,               
                folder_name,        
                caption_text,       
                link_to_caption,    
                None,               
                None,               
                link_transcription, 
                link_text,          
                link_summary,       
            ),
        )

        print(f"   Row inserted for '{folder_name}'")

    cur.close()
    conn.close()
    print("\n DONE: all videos inserted into table 'Videos'.")


if __name__ == "__main__":
    populate_videos_from_dataset()
