import importlib.util
import sys
from pathlib import Path

from textual.screen import Screen
from textual.widgets import Markdown

SLIDE_EXTS = (".md", ".MD", ".py")


def load_slide(path: Path) -> type[Screen]:
    """Load a single slide file (markdown or python Textual screen) as a Screen."""
    path = Path(path)
    if path.suffix in (".md", ".MD"):
        return _markdown_slide(path.read_text())
    if path.suffix == ".py":
        return _python_slide(path)
    raise ValueError(f"Unsupported slide type: {path.suffix}")


def load_deck(directory: Path) -> list[tuple[str, type[Screen]]]:
    """Load all slides in a directory, sorted by filename."""
    slides = []
    for path in sorted(Path(directory).iterdir()):
        if path.name == "__init__.py":
            continue
        if path.suffix not in SLIDE_EXTS:
            continue
        slides.append((path.name, load_slide(path)))
    return slides


def _markdown_slide(content: str) -> type[Screen]:
    class Slide(Screen):
        def compose(self):
            yield Markdown(content, id="markdown")

    return Slide


def _python_slide(path: Path) -> type[Screen]:
    spec = importlib.util.spec_from_file_location(f"termdeck_slide_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Slide


def main() -> None:
    if len(sys.argv) > 1:
        deck_dir = Path(sys.argv[1])
    else:
        deck_dir = Path(__file__).parent / "sample"

    if not deck_dir.is_dir():
        sys.exit(f"error: not a directory: {deck_dir}")

    slides = load_deck(deck_dir)
    if not slides:
        sys.exit(f"error: no slides (.md/.py) found in {deck_dir}")

    from termdeck.app import TermDeck

    TermDeck(deck_dir).run()


if __name__ == "__main__":
    main()
