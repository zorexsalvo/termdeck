import json
import time
from pathlib import Path

from textual import events
from textual.app import App
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Markdown, Static

from termdeck.deck import _get_state_path, _write_state, load_deck


class TermDeckNotes(App):
    """Presenter notes companion for TermDeck."""

    title = "TermDeck Notes"
    CSS_PATH = str(Path(__file__).parent / "styles" / "default.tcss")
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("r", "reset", "Reset timer"),
    ]

    slide_index = reactive(0)
    total_start = reactive(0.0)
    slide_start = reactive(0.0)

    def __init__(self, deck_dir: Path, slides=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deck_dir = Path(deck_dir)
        self.state_path = _get_state_path(deck_dir)
        self._slides = slides if slides is not None else load_deck(self.deck_dir)
        self._total_elapsed = 0.0
        self._slide_elapsed = 0.0

    def compose(self):
        yield Header()
        with VerticalScroll(id="notes-container"):
            yield Static(id="info-bar")
            yield Markdown(id="notes-content")
            yield Static(id="next-slide-bar")
        yield Footer()

    def on_mount(self):
        self.set_interval(0.2, self._poll_state)
        self.set_interval(1.0, self._update_timer)
        self._poll_state()

    def _poll_state(self):
        if not self.state_path.exists():
            self._set_waiting()
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            new_index = data.get("slide", 0)
            if new_index != self.slide_index:
                self.slide_index = new_index
            self.total_start = data.get("total_start_time", time.time())
            self.slide_start = data.get("slide_start_time", time.time())
            self._update_elapsed()
            self._update_display()
        except Exception:
            self._set_waiting()

    def _update_timer(self):
        self._update_elapsed()
        self._update_display()

    def _update_elapsed(self):
        now = time.time()
        self._total_elapsed = now - self.total_start
        self._slide_elapsed = now - self.slide_start

    def _format_time(self, seconds: float) -> str:
        if seconds < 0:
            seconds = 0
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    def _set_waiting(self):
        info = self.query_one("#info-bar", Static)
        info.update("Waiting for presentation to start…")
        content = self.query_one("#notes-content", Markdown)
        content.update("")
        next_bar = self.query_one("#next-slide-bar", Static)
        next_bar.update("")

    def _update_display(self):
        if not self._slides:
            return

        info = self.query_one("#info-bar", Static)
        total_fmt = self._format_time(self._total_elapsed)
        slide_fmt = self._format_time(self._slide_elapsed)
        info.update(
            f"Slide {self.slide_index + 1} / {len(self._slides)}  |  "
            f"Total {total_fmt}  |  Current {slide_fmt}"
        )

        notes = self._slides[self.slide_index][2] if self.slide_index < len(self._slides) else ""
        content = self.query_one("#notes-content", Markdown)
        content.update(notes or "*No notes for this slide.*")

        next_bar = self.query_one("#next-slide-bar", Static)
        if self.slide_index < len(self._slides) - 1:
            next_bar.update(f"Next: {self._slides[self.slide_index + 1][0]}")
        else:
            next_bar.update("(end of deck)")

    def _navigate(self, delta: int) -> None:
        new_index = self.slide_index + delta
        if not (0 <= new_index < len(self._slides)):
            return
        self.slide_index = new_index
        self.slide_start = time.time()
        _write_state(
            self.state_path,
            self.slide_index,
            self._slides[self.slide_index][0],
            self.total_start,
            self.slide_start,
        )
        self._update_display()

    def action_reset(self) -> None:
        """Reset timer and jump to first slide."""
        now = time.time()
        self.slide_index = 0
        self.total_start = now
        self.slide_start = now
        _write_state(
            self.state_path,
            0,
            self._slides[0][0],
            self.total_start,
            self.slide_start,
        )
        self._update_display()

    def on_key(self, event: events.Key) -> None:
        if event.key == "right":
            self._navigate(1)
        elif event.key == "left":
            self._navigate(-1)
        elif event.key == "r":
            self.action_reset()
        else:
            return
