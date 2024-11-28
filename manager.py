import os
import base64
import json
from tools import get_image_items
from itertools import chain


class Manager:
    def __init__(self) -> None:
        print("Initializing manager...")
        # Load data
        with open("khan-academy-data.json") as fp:
            data = json.load(fp)

        khanacademy = [
            {**img, "url": img["options"]["backgroundImage"]["url"]}
            for img in get_image_items(data)
            if "options" in img
            and img["options"]["backgroundImage"]["url"].endswith(".png")
        ]
        cracksat = []
        for subdirs, _, files in os.walk("cracksat-images"):
            for fp in files:
                with open(f"cracksat-images/{fp}", "rb") as f:
                    cracksat.append(
                        {"id": fp, "url": f.read()}
                    )

        self.data = [*khanacademy, *cracksat]

        self.registeration = {}
        self.load()

        work_done = list(chain.from_iterable(self.registeration.values()))
        self.data = [d for d in self.data if d not in work_done]

        with open("labeler.html", "r") as fp:
            self.labeler = fp.read()
        print("Manager initialized...")

    def load(self):
        if not os.path.exists("work.json"):
            self.save()
            return

        with open("work.json", "r") as f:
            self.registeration = json.load(f)

    def load_image(self, email: str):
        if email not in self.registeration:
            self.registeration[email] = []

        img = self.data.pop()
        self.registeration[email].append(img["id"])
        self.save()
        return img

    def save(self):
        with open("work.json", "w") as f:
            json.dump(self.registeration, f)


manager = Manager()
