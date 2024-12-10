import os
import csv
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

        self.registeration = self.load_registeration()

        self.data = {}
        work_done = list(chain.from_iterable(self.registeration.values()))
        for subdir, _, files in os.walk("data"):
            if [f for f in files if f.endswith(".png")]:
                self.data[subdir] = []
            else:
                continue
            
            for fp in files:
                with open(f"{subdir}/{fp}", "rb") as f:
                    if not fp in work_done:
                        self.data[subdir].append(
                            {"id": fp, "url": f.read()}
                        )

        with open("data/khanacademy/descriptions.csv", "r") as f:
            self.descriptions = {r["index"]: r["desc"] for r in csv.DictReader(f)}

        self.lookback = {}

        self.labeler_html, self.viewer_html = self.load_html()
        self.work = self.load_review_data()

        print("Manager initialized...")

    def load_html(self):
        with open("labeler.html", "r") as fp:
            labeler_html = fp.read()

        with open("viewer.html", "r") as fp:
            viewer_html = fp.read()
        return labeler_html, viewer_html

    def load_review_data(self):
        work = []
        for _, _, files in os.walk("work"):
            for fp in files:
                with open(f"work/{fp}", "r") as f:
                    work.append(json.load(f))
        return work

    def load_registeration(self):
        if not os.path.exists("work.json"):
            self.save()
            return {}

        with open("work.json", "r") as f:
            return json.load(f)

    def load_image(self, category: str, email: str, save=False):
        with open("background.jpg", "rb") as f:
            return {"url": f.read(), "id": "1"}
        if email not in self.registeration:
            self.registeration[email] = []

        img = self.data[category].pop()
        
        if save:
            self.registeration[email].append(img["id"])
            self.lookback[img["id"]] = img
            self.save()
        return img

    def load_previous_image(self, email: str) -> dict:
        try:
            img = self.lookback[self.registeration[email][-1]]
        except Exception:
            img = None

        return img

    def save(self):
        with open("work.json", "w") as f:
            json.dump(self.registeration, f)


manager = Manager()
