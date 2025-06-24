#!/usr/bin/env python3
import os
import shutil
from bs4 import BeautifulSoup

# === CONFIG ===
# 1) Root containing all your experiment directories:
BASE_DIR     = r"C:\Users\anmol\OneDrive\Desktop\IIT Hyderabad"

# 2) Folder where your bot assets live:
ASSETS_DIR   = r"C:\Users\anmol\OneDrive\Desktop\IIT Hyderabad\chatbot"

# 3) Your HTML snippet file:
SNIPPET_PATH = os.path.join(ASSETS_DIR, "chatbot.html")

# 4) List all asset filenames you want copied alongside the snippet:
ASSET_FILES = ["chatbot.js", "chatbot.css"]  # add more if needed
# ================

# Read the snippet once
with open(SNIPPET_PATH, encoding="utf-8") as f:
    snippet_html = f.read().strip()

for root, dirs, files in os.walk(BASE_DIR):
    # look for any simulation/index.html
    if root.endswith(os.path.join("simulation")) and "index.html" in files:
        # 1) copy asset files into this folder
        for fname in ASSET_FILES:
            src = os.path.join(ASSETS_DIR, fname)
            dst = os.path.join(root, fname)
            shutil.copy(src, dst)

        # 2) parse & inject into index.html
        idx_path = os.path.join(root, "index.html")
        with open(idx_path, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # skip if already injected
        if soup.find(id="chatbot-container"):
            continue

        # append snippet before </body>
        if soup.body:
            snippet_soup = BeautifulSoup(snippet_html, "html.parser")
            soup.body.append(snippet_soup)
        else:
            # fallback: append at end of file
            snippet_soup = BeautifulSoup(snippet_html, "html.parser")
            soup.append(snippet_soup)

        # write back out
        with open(idx_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

print("✅ Finished injecting chatbot into all simulation/index.html files.")
