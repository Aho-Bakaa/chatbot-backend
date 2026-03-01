import os
import shutil
from bs4 import BeautifulSoup

BASE_DIR= r"C:\Users\anmol\OneDrive\Desktop"

ASSETS_DIR= r"C:\Users\anmol\OneDrive\Desktop\chatbot"

SNIPPET_PATH= os.path.join(ASSETS_DIR, "chatbot.html")

ASSET_FILES = ["chatbot.js", "chatbot.css"]  

with open(SNIPPET_PATH, encoding="utf-8") as f:
    snippet_html = f.read().strip()

for root, dirs, files in os.walk(BASE_DIR):
    if root.endswith(os.path.join("simulation")) and "index.html" in files:
        for fname in ASSET_FILES:
            src = os.path.join(ASSETS_DIR, fname)
            dst = os.path.join(root, fname)
            shutil.copy(src, dst)

        idx_path = os.path.join(root, "index.html")
        with open(idx_path, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        if soup.find(id="chatbot-container"):
            continue

        if soup.body:
            snippet_soup = BeautifulSoup(snippet_html, "html.parser")
            soup.body.append(snippet_soup)
        else:
            snippet_soup = BeautifulSoup(snippet_html, "html.parser")
            soup.append(snippet_soup)

        with open(idx_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

print(" Finished injecting chatbot into all simulation/index.html files.")


