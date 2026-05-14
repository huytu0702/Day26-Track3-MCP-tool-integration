from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
SCREENSHOTS = [
    ("mcp-inspector.txt", "MCP Inspector running with sqlite-lab server", "01-mcp-inspector-running.png"),
    ("verify-server.txt", "Verification script: resources, tools, and safe errors", "02-verify-server.png"),
    ("http-auth.txt", "HTTP bearer auth demo", "03-http-auth.png"),
    ("tests-coverage.txt", "Automated tests and coverage", "04-tests-coverage.png"),
]


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def render_text(source: str, title: str, output: str) -> None:
    text = (ROOT / source).read_text(encoding="utf-8", errors="replace")
    lines = []
    for line in text.splitlines()[:70]:
        lines.extend(textwrap.wrap(line, width=110) or [""])
    lines = lines[:90]

    title_font = load_font(26)
    body_font = load_font(17)
    line_height = 23
    padding = 28
    width = 1500
    height = padding * 2 + 42 + max(1, len(lines)) * line_height

    image = Image.new("RGB", (width, height), "#0f172a")
    draw = ImageDraw.Draw(image)
    draw.text((padding, padding), title, fill="#e2e8f0", font=title_font)
    y = padding + 48
    for line in lines:
        draw.text((padding, y), line, fill="#cbd5e1", font=body_font)
        y += line_height

    image.save(ROOT / output)


for source, title, output in SCREENSHOTS:
    render_text(source, title, output)
    print(f"Created {output}")
