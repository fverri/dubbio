from urllib.request import urlopen
import subprocess
import json
import base64
import os
from openai import OpenAI
from dotenv import find_dotenv, dotenv_values
from video_uploader import authenticate_youtube, upload_video
import time
from datetime import datetime, timedelta, timezone
from chat_to_images import chat_to_images
from chat_to_speeches import chat_to_speeches
from images_and_speeches_to_video import images_and_speeches_to_video

CACHE_FILE = "conversation_cache.json"
CACHE_SIZE = 10

GENERATE_AT = (5, 0)

UPLOAD_TIMES = ((17, 0), (21, 0))

env_path = find_dotenv(usecwd=True)
values = dotenv_values(env_path)

client = OpenAI(api_key=(values.get("OPENAI_API_KEY")))


def call_llm(system_prompt, user_prompt, response_format):
    kwargs = {}
    if response_format is not None:
        kwargs["response_format"] = response_format

    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs,
    )

    content = response.choices[0].message.content
    if response_format and response_format.get("type") == "json_object":
        return json.loads(content)
    return content.strip()


def load_cache():
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_video(video_number):
    start_time = time.time()
    part_start = start_time

    with open("prompts/json_system_prompt.txt", "r", encoding="utf-8") as f:
        json_system_prompt = f.read().strip()
    with open("prompts/json_user_prompt.txt", "r", encoding="utf-8") as f:
        raw_json_user_prompt = f.read().strip()

    cache = load_cache()
    recent_desc = list(reversed(cache))
    attempts_json = json.dumps(recent_desc, ensure_ascii=False, indent=2)

    json_user_prompt = raw_json_user_prompt.replace("{{CHAT_JSON}}", attempts_json)

    configuration = call_llm(
        json_system_prompt, json_user_prompt, response_format={"type": "json_object"}
    )

    cache = load_cache()
    cache.append(configuration)
    if len(cache) > CACHE_SIZE:
        cache = cache[-CACHE_SIZE:]

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    with open("configuration.json", "w", encoding="utf-8") as f:
        json.dump(configuration, f, ensure_ascii=False, indent=4)

    print(
        f"Generated configuration in {time.time() - part_start:.2f} seconds: {configuration}"
    )

    print(f"Total so far: {time.time() - start_time:.2f} seconds")

    part_start = time.time()

    with open("prompts/image_system_prompt.txt", "r", encoding="utf-8") as f:
        image_system_prompt = f.read().strip()

    with open("prompts/image_user_prompt.txt", "r", encoding="utf-8") as f:
        image_user_prompt_tpl = f.read()

    chat_json_str = json.dumps(configuration, ensure_ascii=False)
    image_user_prompt = image_user_prompt_tpl.replace("{{CHAT_JSON}}", chat_json_str)

    image_prompt_text = call_llm(
        image_system_prompt, image_user_prompt, response_format=None
    )

    print(
        f"Generated profile image prompt in {time.time() - part_start:.2f} seconds: {image_prompt_text}"
    )

    print(f"Total so far: {time.time() - start_time:.2f} seconds")

    part_start = time.time()

    img = client.images.generate(
        model="gpt-image-1.5", prompt=image_prompt_text, size="1024x1024"
    )

    image_base64 = img.data[0].b64_json

    with open("profile_image.png", "wb") as f:
        f.write(base64.b64decode(image_base64))

    print(f"Generated profile image in {time.time() - part_start:.2f} seconds")

    print(f"Total so far: {time.time() - start_time:.2f} seconds")

    part_start = time.time()

    chat_to_images()

    print(f"Generated images in {time.time() - part_start:.2f} seconds")

    print(f"Total so far: {time.time() - start_time:.2f} seconds")

    part_start = time.time()

    chat_to_speeches()

    print(f"Generated speeches in {time.time() - part_start:.2f} seconds")

    print(f"Total so far: {time.time() - start_time:.2f} seconds")

    part_start = time.time()

    images_and_speeches_to_video(video_number)

    images = os.listdir("images")
    speeches = os.listdir("speeches")

    for file in images:
        if file == ".gitkeep":
            continue

        os.remove(f"images/{file}")

    for file in speeches:
        if file == ".gitkeep":
            continue

        os.remove(f"speeches/{file}")

    os.remove("configuration.json")
    os.remove("profile_image.png")

    print(f"Generated video in {time.time() - part_start:.2f} seconds")

    print(f"Total so far: {time.time() - start_time:.2f} seconds")

    part_start = time.time()

    with open(
        "prompts/title_and_description_system_prompt.txt", "r", encoding="utf-8"
    ) as f:
        yt_system_prompt = f.read().strip()
    with open(
        "prompts/title_and_description_user_prompt.txt", "r", encoding="utf-8"
    ) as f:
        yt_user_prompt_tpl = f.read()

    yt_user_prompt = yt_user_prompt_tpl.replace("{{CHAT_JSON}}", chat_json_str)

    data_url = f"data:image/png;base64,{image_base64}"

    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": yt_system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": yt_user_prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    titles_and_descriptions = [data.get("title", ""), data.get("description", "")]

    print(
        f"Generated YouTube title and description in {time.time() - part_start:.2f} seconds"
    )

    print(f"Title: {titles_and_descriptions[0]}")
    print(f"Description: {titles_and_descriptions[1]}")

    print(f"Total time: {time.time() - start_time:.2f} seconds")

    return titles_and_descriptions


def upload_video_to_youtube(title, description, video_number):
    start_time = time.time()

    youtube = authenticate_youtube()

    video_id = None
    file_path = f"videos/output_video_{video_number}.mp4"
    try:
        video_id = upload_video(
            youtube,
            file_path,
            title=title,
            description=description,
            category_id="22",
        )
    except Exception as e:
        print(f"Error uploading video: {e}")
    finally:
        os.remove(file_path)
        print(
            f"Uploaded video at https://www.youtube.com/shorts/{video_id} in {time.time() - start_time:.2f} seconds"
        )


def start_react_server():
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    proc = subprocess.Popen(
        [npm_cmd, "start"],
        cwd="react_imessage",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    while True:
        try:
            urlopen("http://127.0.0.1:3000")
            break
        except Exception:
            time.sleep(1)

    print("React server is ready at http://127.0.0.1:3000")
    return proc


def stop_react_server(proc):
    proc.terminate()
    proc.wait()
    print("React server stopped")


def convert_time_tuple_to_datetime(time_tuple):
    hour, minute = time_tuple
    now = datetime.now(timezone.utc)
    scheduled_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if scheduled_datetime <= now:
        scheduled_datetime += timedelta(days=1)
    return scheduled_datetime


def wait_until_datetime(target_datetime):
    while True:
        now = datetime.now(timezone.utc)
        remaining_seconds = (target_datetime - now).total_seconds()
        if remaining_seconds <= 0:
            break
        time.sleep(min(remaining_seconds, 10))


def build_upload_schedule_from_time_tuples(time_tuples):
    schedule = [convert_time_tuple_to_datetime(t) for t in time_tuples]
    schedule.sort()
    return schedule


try:
    react_server_process = start_react_server()

    generation_datetime = convert_time_tuple_to_datetime(GENERATE_AT)
    upload_schedule = build_upload_schedule_from_time_tuples(UPLOAD_TIMES)
    NUMBER_OF_VIDEOS = len(upload_schedule)

    print(
        f"Scheduled generation time (UTC): {generation_datetime.hour:02d}:{generation_datetime.minute:02d}"
    )

    print("Scheduled upload times (UTC):")
    for dt in upload_schedule:
        print(f"{dt.hour:02d}:{dt.minute:02d}")

    print(f"Number of videos: {NUMBER_OF_VIDEOS}")

    while True:
        print(
            f"Waiting for generation time (UTC): {generation_datetime.hour:02d}:{generation_datetime.minute:02d}"
        )

        wait_until_datetime(generation_datetime)

        titles_and_descriptions = []

        for video_number in range(NUMBER_OF_VIDEOS):
            print(f"Video {video_number + 1}/{NUMBER_OF_VIDEOS}")
            result = generate_video(video_number)
            titles_and_descriptions.append(result)

        for video_number, scheduled_datetime in enumerate(upload_schedule):
            print(
                f"Waiting for upload time (UTC): {scheduled_datetime.hour:02d}:{scheduled_datetime.minute:02d}",
            )
            wait_until_datetime(scheduled_datetime)
            title, description = titles_and_descriptions[video_number]
            print(f"Uploading video {video_number + 1}/{NUMBER_OF_VIDEOS}")
            upload_video_to_youtube(title, description, video_number)

        generation_datetime += timedelta(days=1)
        upload_schedule = [dt + timedelta(days=1) for dt in upload_schedule]

except KeyboardInterrupt:
    print("Process interrupted by user")
finally:
    stop_react_server(react_server_process)