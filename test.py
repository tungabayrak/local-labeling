import os

for subdir, _, files in os.walk("data/khanacademy"):
    if not "Unit" in subdir:
        continue

    with open(f"{subdir}/{os.path.basename(subdir)}.txt") as f:
        notes = f.read()

    assignments = {}
    for l in notes.split("\n"):
        index, *desc = l.split(".")
        desc = ".".join(desc)
        assignments[index] = desc
    
    
