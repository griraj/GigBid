"""Public project write-up, rendered from the versioned article without scripts."""
import html
import re
from pathlib import Path
from fastapi.responses import HTMLResponse

ROOT=Path(__file__).resolve().parents[2]


def article():
    source=(ROOT/'docs/TECHNICAL_WRITEUP.md').read_text(encoding='utf-8')
    sections=[]
    for paragraph in re.split(r'\n\s*\n',source.strip()):
        text=html.escape(' '.join(paragraph.splitlines()))
        text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
        if text.startswith('## '):sections.append('<h2>'+text[3:]+'</h2>')
        elif text.startswith('# '):sections.append('<h1>'+text[2:]+'</h1>')
        else:sections.append('<p>'+text+'</p>')
    return HTMLResponse('''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GigBid engineering notes: evidence, retrieval and approval</title>
<style>body{margin:0;background:#f8fafc;color:#1c2d43;font:18px/1.75 system-ui,sans-serif}
main{max-width:780px;margin:auto;padding:48px 24px 80px}a{color:#4b38b8}h1{font-size:36px;line-height:1.2}
h2{font-size:25px;margin-top:40px}code{font-size:.86em;overflow-wrap:anywhere}nav{font-size:15px}p{margin:22px 0}
</style></head><body><main><nav><a href="/">GigBid</a> / Engineering notes</nav>'''
        +''.join(sections)+'<p><a href="https://github.com/griraj/GigBid">Source code and experimental evidence</a></p></main></body></html>')
