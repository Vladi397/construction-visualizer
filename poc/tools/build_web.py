"""Makes the web/ folder for publishing as a claude.ai page.

web/index.html   the customer showcase (showcase.html). The host wraps the main page in its own
                 <html>/<head>/<body>, so those wrapper tags are removed here.
web/editor.html  the surface editor (index.html), kept as a full document because extra pages
                 are served as they are.
assets.js is published next to them unchanged.

Run from the poc folder:  python tools/build_web.py
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRAPPER = [
    '<!doctype html>\n', '<html lang="en">\n', '<head>\n', '<meta charset="utf-8">\n',
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n',
    '</head>\n', '<body>\n', '</body>\n', '</html>\n',
]


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def write(name, text):
    os.makedirs(os.path.join(HERE, "web"), exist_ok=True)
    with open(os.path.join(HERE, "web", name), "w", encoding="utf-8") as f:
        f.write(text)


showcase = read("showcase.html")
for tag in WRAPPER:
    assert tag in showcase, f"missing {tag!r}"
    showcase = showcase.replace(tag, "", 1)
# On the web the showcase is the main page and the editor lives next to it.
showcase = showcase.replace('href="index.html" data-link="editor"', 'href="editor.html" data-link="editor"')
write("index.html", showcase)

editor = read("index.html").replace('href="showcase.html" data-link="showcase"', 'href="index.html" data-link="showcase"')
write("editor.html", editor)

print("web/index.html", round(len(showcase) / 1024), "KB, title in first 8 KB:", "<title>" in showcase[:8192])
print("web/editor.html", round(len(editor) / 1024), "KB")
