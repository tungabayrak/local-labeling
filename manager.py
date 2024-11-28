import os
import json
from tools import get_image_items


class Manager:
    def __init__(self) -> None:
        # Load data
        with open("khan-academy-data.json") as f:
            data = json.load(f)

        self.data = get_image_items(data)
        self.registeration = {}
        with open("labeler.html", "r") as f:
            self.labeler = f.read()
        self.load()

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
        self.registeration[email].append(img)
        self.save()
        return img

    def save(self):
        with open("work.json", "w") as f:
            json.dump(self.registeration, f)


manager = Manager()
