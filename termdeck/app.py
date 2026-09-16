import subprocess
import sys
import time
from pathlib import Path

from textual import events
from textual.app import App
from textual.widgets import Footer, Header

from termdeck.deck import ImageFullscreen, ImageWidget, _get_state_path, _write_state, load_deck


def _open_image(path: Path) -> None:
    """Open an image file with the system default viewer."""
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif sys.platform == "win32":
        subprocess.run(["start", str(path)], shell=True, check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


class TermDeck(App):
    """A terminal presentation app: arrow keys walk through a deck of slides."""

    title = "TermDeck"
    CSS_PATH = str(Path(__file__).parent / "styles" / "default.tcss")
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(self, deck_dir: Path, slides=None, *args, **kwargs):
        default_css = Path(__file__).parent / "styles" / "default.tcss"
        custom_css = Path(deck_dir) / "deck.tcss"
        self.CSS_PATH = [str(default_css)]
        if custom_css.is_file():
            self.CSS_PATH.append(str(custom_css))
        super().__init__(*args, **kwargs)
        self.deck_dir = deck_dir
        self.state_path = _get_state_path(deck_dir)
        self._total_start = time.time()
        self._slide_start = self._total_start
        self.slide_number = 0
        loaded = slides if slides is not None else load_deck(deck_dir)
        self.names = [name for name, _, _ in loaded]
        for name, cls, _ in loaded:
            self.install_screen(cls, name)

    def _current_image_path(self) -> Path | None:
        """Return the image path of the current screen, or None."""
        from textual.css.query import NoMatches

        screen = self.screen
        if isinstance(screen, ImageFullscreen):
            return screen.path
        try:
            image = screen.query_one(ImageWidget)
        except NoMatches:
            return None
        return image.path

    def _toggle_fullscreen(self) -> None:
        """Push or pop the fullscreen image view."""
        if isinstance(self.screen, ImageFullscreen):
            self.pop_screen()
            return

        path = self._current_image_path()
        if path is not None:
            self.push_screen(ImageFullscreen(path))

    def _go_to_slide(self, index: int) -> None:
        """Navigate to the slide at index, exiting fullscreen if needed."""
        if isinstance(self.screen, ImageFullscreen):
            self.pop_screen()
        self.slide_number = index
        self._slide_start = time.time()
        _write_state(
            self.state_path,
            self.slide_number,
            self.names[self.slide_number],
            self._total_start,
            self._slide_start,
        )
        self.push_screen(self.names[index])

    def on_key(self, event: events.Key) -> None:
        names = self.names
        if not names:
            return

        if event.key == "right" and self.slide_number < len(names) - 1:
            self._go_to_slide(self.slide_number + 1)
        elif event.key == "left" and self.slide_number > 0:
            self._go_to_slide(self.slide_number - 1)
        elif event.key == "o":
            path = self._current_image_path()
            if path is not None:
                _open_image(path)
        elif event.key == "f":
            self._toggle_fullscreen()
        elif event.key == "escape" and isinstance(self.screen, ImageFullscreen):
            self.pop_screen()
        else:
            return

    def _poll_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            import json
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            new_index = data.get("slide", 0)
            if 0 <= new_index < len(self.names) and new_index != self.slide_number:
                self._go_to_slide(new_index)
        except Exception:
            pass

    def on_mount(self) -> None:
        self.set_interval(0.2, self._poll_state)
        if self.names:
            self._slide_start = time.time()
            _write_state(
                self.state_path,
                0,
                self.names[0],
                self._total_start,
                self._slide_start,
            )
            self.push_screen(self.names[0])

    def compose(self):
        yield Header()
        yield Footer()


if __name__ == "__main__":
    TermDeck(Path("slides")).run()
