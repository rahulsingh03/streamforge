import json
import os
import subprocess
import pymysql
import boto3
import requests
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_UPLOAD_TOPIC = os.getenv("KAFKA_UPLOAD_TOPIC")
KAFKA_PROGRESS_TOPIC = os.getenv("KAFKA_PROGRESS_TOPIC")

AWS_BUCKET = os.getenv("AWS_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def notify_backend(video_id, percentage, message):
    baseUrl = os.getenv("BASE_API_URL")
    print(f'baseUrl {baseUrl}')
    requests.post(
        f"{baseUrl}api/videos/internal/progress/{video_id}",
        json={
            "progress_percent": percentage,
            "progress_message": message
        }
    )

def mysql_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
        cursorclass=pymysql.cursors.DictCursor
    )

def update_video_status(video_id, status, thumbnail_path=None, duration=None, resolution=None, error=None):
    conn = mysql_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                UPDATE videos
                SET status=%s,
                    thumbnail_path=%s,
                    duration=%s,
                    resolution=%s,
                    error_message=%s,
                    updated_at=NOW()
                WHERE id=%s
            """
            cursor.execute(sql, (status, thumbnail_path, duration, resolution, error, video_id))
        conn.commit()
    finally:
        conn.close()

def download_from_s3(s3_key, local_path):
    s3.download_file(AWS_BUCKET, s3_key, local_path)

def upload_to_s3(local_path, s3_key):
    s3.upload_file(local_path, AWS_BUCKET, s3_key)

def extract_metadata(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    stream = data["streams"][0]
    width = stream.get("width")
    height = stream.get("height")
    duration = float(stream.get("duration", 0))

    resolution = f"{width}x{height}"
    return int(duration), resolution

def generate_thumbnail(video_path, thumbnail_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ss", "00:00:01",
        "-vframes", "1",
        thumbnail_path
    ]
    subprocess.run(cmd, capture_output=True)

def process_video_event(event):
    video_id = event["video_id"]
    s3_key = event["s3_key"]

    print(f"Processing video_id={video_id}, s3_key={s3_key}")

    local_video_path = f"/tmp/video_{video_id}.mp4"
    local_thumb_path = f"/tmp/thumb_{video_id}.jpg"

    try:
        update_video_status(video_id, "processing")

        # Download video
        notify_backend(video_id, 10, "Downloading from S3")
        download_from_s3(s3_key, local_video_path)

        # Extract metadata
        notify_backend(video_id, 40, "Extracting metadata")
        duration, resolution = extract_metadata(local_video_path)

        # Generate thumbnail
        notify_backend(video_id, 70, "Generating thumbnail")
        generate_thumbnail(local_video_path, local_thumb_path)

        # Upload thumbnail
        notify_backend(video_id, 100, "Processing completed")
        thumb_s3_key = f"videos/thumbnails/{video_id}/thumb.jpg"
        upload_to_s3(local_thumb_path, thumb_s3_key)

        update_video_status(
            video_id,
            "completed",
            thumbnail_path=thumb_s3_key,
            duration=duration,
            resolution=resolution
        )

        print(f"Video {video_id} completed successfully.")

    except Exception as e:
        update_video_status(video_id, "failed", error=str(e))
        notify_backend(video_id, 0, str(e))
        print(f"Video {video_id} failed: {str(e)}")

def main():
    consumer = KafkaConsumer(
        KAFKA_UPLOAD_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id="streamforge-worker",
        session_timeout_ms=30000,
        max_poll_interval_ms=600000,
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    print(f"Worker listening on Kafka topic: {KAFKA_UPLOAD_TOPIC}")

    for msg in consumer:
        event = msg.value
        if event.get("event") == "video.uploaded":
            process_video_event(event)
            consumer.commit()

if __name__ == "__main__":
    main()