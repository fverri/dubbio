import json
import shutil
import os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np


def _generate_image(chat, block_number, message_number):
    image = f"images/image_{block_number}_{message_number}.png"
    no_max_height_image = (
        f"images/no_max_height_image_{block_number}_{message_number}.png"
    )
    react_imessage_chat = "react_imessage/public/chat.json"

    with open(react_imessage_chat, "w", encoding="utf-8") as file:
        json.dump({"messages": chat["messages"]}, file, indent=4, ensure_ascii=False)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}, device_scale_factor=2
        )

        page = context.new_page()
        page.goto("http://localhost:3000/", wait_until="load")

        chat_box = page.query_selector(".chat-box")

        chat_box.screenshot(path=image, type="png")

        page.add_style_tag(content=".imessage { max-height: none !important; }")
        chat_box.screenshot(path=no_max_height_image, type="png")

        browser.close()

    image_file = Image.open(image)
    if image_file.width > 860:
        raise ValueError()

    no_max_height_image_file = Image.open(no_max_height_image)

    image_array = np.array(image_file)
    no_max_height_image_array = np.array(no_max_height_image_file)

    if image_array.shape != no_max_height_image_array.shape:
        difference = True
    else:
        difference = not np.array_equal(image_array, no_max_height_image_array)

    if difference and len(chat["messages"]) == 1:
        raise ValueError()

    if not difference:
        os.remove(no_max_height_image)
        return True

    os.remove(image)
    os.remove(no_max_height_image)

    return False


def chat_to_images() -> None:
    with open("configuration.json", "r", encoding="utf-8") as file:
        chat_data = json.load(file)

    messages = chat_data.get("messages", [])
    profile_name = chat_data.get("profile_name", "Usuario")

    profile_name_path = "react_imessage/public/profile_name.json"
    with open(profile_name_path, "w", encoding="utf-8") as file:
        json.dump({"profileName": profile_name}, file, indent=4, ensure_ascii=False)

    block_number = 1

    shutil.copy("profile_image.png", "react_imessage/public/")

    while messages:
        block = []
        message_number = 1
        i = 0

        while i < len(messages):
            block.append(messages[i])

            try:
                valid = _generate_image(
                    {"messages": block}, block_number, message_number
                )
            except ValueError as e:
                print(e)
                return

            if valid:
                message_number += 1
                i += 1
            else:
                block.pop()
                break

        if block:
            block_number += 1
            messages = messages[len(block) :]
        else:
            messages = messages[1:]

    os.remove("react_imessage/public/chat.json")
    os.remove("react_imessage/public/profile_name.json")
    os.remove("react_imessage/public/profile_image.png")