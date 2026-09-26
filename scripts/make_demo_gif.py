"""Render docs/demo.gif: a terminal-style animation of the offline simulator.

No external tools (asciinema, ttygif, etc.) are used. This renders each
terminal frame directly with Pillow and drives the same Brain/ToolExecutor
used by `python -m receptionist.simulate`, so the recording matches the real
offline demo exactly.

Run with: python scripts/make_demo_gif.py
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from receptionist.brain import Brain  # noqa: E402
from receptionist.config import load_config  # noqa: E402
from receptionist.simulate import SCRIPT  # noqa: E402
from receptionist.tools import ToolExecutor  # noqa: E402

WIDTH, HEIGHT = 860, 520
FONT_SIZE = 16
LINE_HEIGHT = 22
MARGIN = 20
BG_COLOR = (13, 17, 23)
TITLE_BAR = (33, 38, 45)
PROMPT_COLOR = (88, 166, 255)
REPLY_COLOR = (126, 231, 135)
TEXT_COLOR = (201, 209, 217)
WRAP_WIDTH = 78

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_transcript() -> list[tuple[str, str]]:
    """Drive the real simulator brain and collect (speaker, text) lines."""
    config = load_config(REPO_ROOT / "business.example.yaml")
    executor = ToolExecutor(config, call_sid="demo", dry_run=True)
    brain = Brain(executor=executor, config=config)

    transcript: list[tuple[str, str]] = [("bot", brain.greeting())]
    for caller_line in SCRIPT:
        transcript.append(("you", caller_line))
        reply = brain.respond(caller_line)
        transcript.append(("bot", reply))
        if brain.done:
            break
    return transcript


def wrapped_lines(speaker: str, text: str) -> list[str]:
    prefix = "You: " if speaker == "you" else "Bot: "
    wrapped = textwrap.wrap(text, width=WRAP_WIDTH - len(prefix), subsequent_indent=" " * len(prefix)) or [""]
    wrapped[0] = prefix + wrapped[0]
    return wrapped


def render_frame(font: ImageFont.FreeTypeFont, header: str, lines: list[tuple[str, str]]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)

    draw.rectangle([0, 0, WIDTH, 34], fill=TITLE_BAR)
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([16 + i * 22, 12, 28 + i * 22, 24], fill=color)
    draw.text((WIDTH / 2, 17), header, font=font, fill=TEXT_COLOR, anchor="mm")

    y = 34 + MARGIN
    for speaker, line in lines:
        color = PROMPT_COLOR if speaker == "you" else REPLY_COLOR
        draw.text((MARGIN, y), line, font=font, fill=color)
        y += LINE_HEIGHT
        if y > HEIGHT - LINE_HEIGHT:
            break
    return image


def build_frames() -> list[Image.Image]:
    font = load_font(FONT_SIZE)
    transcript = build_transcript()
    header = "python -m receptionist.simulate"

    rendered_lines: list[tuple[str, str]] = []
    frames: list[Image.Image] = []

    for speaker, text in transcript:
        for wrapped in wrapped_lines(speaker, text):
            rendered_lines.append((speaker, wrapped))
            visible = rendered_lines[-((HEIGHT - 34 - MARGIN) // LINE_HEIGHT):]
            frames.append(render_frame(font, header, visible))

    return frames


def main() -> None:
    frames = build_frames()
    if not frames:
        raise SystemExit("No frames rendered")

    durations = [450] * len(frames)
    durations[-1] = 2500

    out_path = REPO_ROOT / "docs" / "demo.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size_kb = out_path.stat().st_size / 1024
    print(f"Wrote {out_path} ({size_kb:.0f} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
