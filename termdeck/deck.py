import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Type

from markdown_it import MarkdownIt
from textual.containers import Center, VerticalScroll
from textual.screen import Screen
from textual.widgets import Markdown
from textual_image.renderable import Image as AutoRenderable
from textual_image.renderable._protocol import ImageRenderable
from textual_image.renderable.halfcell import Image as HalfcellRenderable
from textual_image.renderable.sixel import Image as SixelRenderable
from textual_image.renderable.tgp import Image as TGPRenderable
from textual_image.renderable.unicode import Image as UnicodeRenderable
from textual_image.widget._base import Image as BaseImage

SLIDE_EXTS = (".md", ".MD", ".py")

_NOTE_PATTERN = re.compile(r"^\s*<!--\s*note(?:s)?\s*:\s*(.*?)\s*-->\s*$", re.IGNORECASE | re.MULTILINE)


def _parse_img_tag(html: str) -> dict[str, str] | None:
    """Parse a standalone <img> tag and return its attributes, or None."""
    stripped = html.strip()
    if not stripped.lower().startswith("<img"):
        return None

    class Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.attrs: dict[str, str] | None = None

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "img" and self.attrs is None:
                self.attrs = {k: (v or "") for k, v in attrs}

    parser = Parser()
    try:
        parser.feed(stripped)
    except Exception:
        return None
    return parser.attrs


_IMAGE_RENDERERS: dict[str, Type[ImageRenderable]] = {
    "kitty": TGPRenderable,
    "tgp": TGPRenderable,
    "sixel": SixelRenderable,
    "halfcell": HalfcellRenderable,
    "unicode": UnicodeRenderable,
}


def _get_image_renderable() -> Type[ImageRenderable]:
    """Return the image renderable selected by TERMDECK_IMAGE_PROTOCOL, or auto."""
    protocol = os.environ.get("TERMDECK_IMAGE_PROTOCOL", "auto").lower()
    if protocol in _IMAGE_RENDERERS:
        return _IMAGE_RENDERERS[protocol]
    return AutoRenderable


def _extract_notes(content: str) -> str:
    """Extract presenter notes from block-level HTML comments."""
    notes = [m.group(1).strip() for m in _NOTE_PATTERN.finditer(content)]
    return "\n\n".join(notes)


def _get_state_path(deck_dir: Path) -> Path:
    """Return the path to the shared state file for a deck directory."""
    h = hashlib.sha256(str(Path(deck_dir).resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"termdeck-{h}.json"


def _write_state(path: Path, slide: int, name: str, total_start: float, slide_start: float) -> None:
    """Atomically write the current presentation state to a JSON file."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({
            "slide": slide,
            "name": name,
            "total_start_time": total_start,
            "slide_start_time": slide_start,
        }),
        encoding="utf-8",
    )
    tmp.replace(path)


def load_slide(path: Path) -> type[Screen]:
    """Load a single slide file (markdown or python Textual screen) as a Screen."""
    path = Path(path)
    if path.suffix in (".md", ".MD"):
        return _markdown_slide(path)
    if path.suffix == ".py":
        return _python_slide(path)
    raise ValueError(f"Unsupported slide type: {path.suffix}")


def load_deck(directory: Path) -> list[tuple[str, type[Screen], str]]:
    """Load all slides in a directory, sorted by filename.

    Returns a list of (filename, Screen class, notes) tuples.
    """
    slides = []
    for path in sorted(Path(directory).iterdir()):
        if path.name == "__init__.py":
            continue
        if path.suffix not in SLIDE_EXTS:
            continue
        notes = ""
        if path.suffix in (".md", ".MD"):
            notes = _extract_notes(path.read_text())
        slides.append((path.name, load_slide(path), notes))
    return slides


def _markdown_slide(path: Path) -> type[Screen]:
    """Build a Screen from a Markdown file, rendering image-only paragraphs as images."""
    path = Path(path)
    content = path.read_text()
    base_dir = path.parent
    segments = _split_markdown(content, base_dir)

    class Slide(Screen):
        def compose(self):
            with VerticalScroll(id="markdown-slide"):
                for seg_type, seg_data in segments:
                    if seg_type == "markdown":
                        yield Markdown(seg_data)
                    elif seg_type == "image":
                        img_path, width, height = seg_data
                        with Center():
                            yield ImageWidget(img_path, width=width, height=height)

    return Slide


def _split_markdown(content: str, base_dir: Path) -> list[tuple[str, Path | str | tuple[Path, str | None, str | None]]]:
    """Split markdown into text chunks and image blocks.

    Paragraphs that contain only a single image token become ("image", path).
    Standalone HTML <img> tags become ("image", (path, width, height)).
    Everything else becomes ("markdown", text_chunk).
    """
    tokens = MarkdownIt().parse(content)
    lines = content.splitlines()
    images: list[tuple[int, int, Path, str | None, str | None]] = []

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "paragraph_open" and token.level == 0 and token.map is not None:
            inline = tokens[i + 1] if i + 1 < len(tokens) else None
            if inline is not None and inline.type == "inline" and inline.children:
                children = [
                    child
                    for child in inline.children
                    if child.type != "text" or child.content.strip()
                ]
                if len(children) == 1 and children[0].type == "image":
                    src = children[0].attrs.get("src", "")
                    img_path = _resolve_image_path(src, base_dir)
                    start, end = token.map
                    images.append((start, end, img_path, None, None))
        elif token.type == "html_block" and token.map is not None:
            attrs = _parse_img_tag(token.content)
            if attrs:
                src = attrs.get("src", "")
                if src:
                    img_path = _resolve_image_path(src, base_dir)
                    start, end = token.map
                    images.append((start, end, img_path, attrs.get("width"), attrs.get("height")))
        i += 1

    segments: list[tuple[str, Path | str | tuple[Path, str | None, str | None]]] = []
    last_end = 0
    for start, end, img_path, width, height in images:
        before = "\n".join(lines[last_end:start])
        if before.strip():
            segments.append(("markdown", before))
        segments.append(("image", (img_path, width, height)))
        last_end = end

    after = "\n".join(lines[last_end:])
    if after.strip():
        segments.append(("markdown", after))

    return segments


def _resolve_image_path(src: str, base_dir: Path) -> Path:
    """Resolve an image src to an absolute path."""
    path = Path(src)
    if path.is_absolute():
        return path
    return base_dir / path


def _python_slide(path: Path) -> type[Screen]:
    spec = importlib.util.spec_from_file_location(f"termdeck_slide_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Slide


class ImageWidget(BaseImage, Renderable=_get_image_renderable()):
    """A widget that renders an image file using the best available terminal graphics method."""

    def __init__(self, path: Path, width: str | None = None, height: str | None = None, **kwargs):
        super().__init__(path, **kwargs)
        self.path = Path(path)
        if width:
            self.styles.width = width
        if height:
            self.styles.height = height


class ImageFullscreen(Screen):
    """A full-screen view of a single image."""

    def __init__(self, path: Path, **kwargs):
        super().__init__(**kwargs)
        self.path = Path(path)

    def compose(self):
        yield ImageWidget(self.path, id="fullscreen-image")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Terminal presentations")
    parser.add_argument("deck_dir", nargs="?", default=None, help="Directory of slides")
    parser.add_argument("--notes", action="store_true", help="Open presenter notes companion")
    args = parser.parse_args()

    if args.deck_dir is None:
        deck_dir = Path(__file__).parent / "sample"
    else:
        deck_dir = Path(args.deck_dir)

    if not deck_dir.is_dir():
        sys.exit(f"error: not a directory: {deck_dir}")

    slides = load_deck(deck_dir)
    if not slides:
        sys.exit(f"error: no slides (.md/.py) found in {deck_dir}")

    if args.notes:
        from termdeck.notes_app import TermDeckNotes
        TermDeckNotes(deck_dir, slides=slides).run()
    else:
        from termdeck.app import TermDeck
        TermDeck(deck_dir, slides=slides).run()


if __name__ == "__main__":
    main()
