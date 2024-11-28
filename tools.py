import json
import os
import base64
from anthropic import Anthropic
from typing import Literal
from openai import OpenAI
import requests
from dotenv import load_dotenv

load_dotenv()

anthropic_client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
)
ANTHROPIC_MODELS = ["claude-3-5-sonnet-latest"]

LLM = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

DATA_JSON_URL = "https://cdn.kastatic.org/ka-perseus-graphie/{id}-data.json"
BASE_IMAGE_URL = "https://cdn.kastatic.org/ka-perseus-graphie/{id}.svg"


def get_image_items(data: dict):
    img_items = []
    for id, obj in data.items():
        widgets = obj["itemData"]["question"]["widgets"]

        for w, w_obj in widgets.items():
            if not w.startswith("image"):
                continue
            img_items.append(w_obj)
    return img_items


def llm_generate(
    prompt: str | None,
    image: bytes | str | None = None,
    system: str | None = None,
    model: (
        Literal["gpt-4o"]
        | Literal["gpt-4o-mini"]
        | Literal["o1-preview"]
        | Literal["claude-3-5-sonnet-latest"]
    ) = "gpt-4o-mini",
    messages=None,
):
    """
    Generates a ChatGPT response on a given prompt with context.

    prompt: str
        the prompt passed to the LLM
    image: bytes | str | None
        image binary data or base64 string
    system: str
        system prompt
    messages: list[str]
        LLM model valid list of messages/histories, if the message is provided
        the prompt, image and system kwargs are ignored.

    Returns (prompt, response)
    """
    if not messages:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        if isinstance(image, bytes):
            image = base64.b64encode(image).decode("utf-8")

        if model in ANTHROPIC_MODELS:
            # anthropic style image object
            image_record = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image,
                },
            }
        else:
            # openai style image objec
            image_record = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image}",
                },
            }

        if prompt:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        [{"type": "text", "text": prompt}, image_record]
                        if image
                        else prompt
                    ),
                }
            )
        elif image:
            messages.append({"role": "user", "content": [image_record]})

    if model in ANTHROPIC_MODELS:
        preponse = anthropic_client.messages.create(
            model=model,
            max_tokens=1024,
            messages=messages,
        )
        response = preponse.content[-1].text  # type: ignore
    else:
        response: str = (
            LLM.chat.completions.create(
                model=model,
                messages=messages,
            )
            .choices[0]
            .message.content
        )  # type: ignore

        if system:
            prompt = str(system) + "\n\n" + str(prompt)

    return prompt, response


def main():
    with open("khan-academy-data.json") as f:
        data = json.load(f)

    for id, obj in data.items():
        widgets = obj["itemData"]["question"]["widgets"]

        for w, w_obj in widgets.items():
            if not w.startswith("image"):
                continue

            img_id = os.path.basename(w_obj["backgroundImage"]["url"])

            requests.get(DATA_JSON_URL.format(id=img_id))
            requests.get(BASE_IMAGE_URL.format(id=img_id))
