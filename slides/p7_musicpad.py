from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Grid
from textual.widgets import Button, Static
from musicpy import C, drum, play


class Slide(Screen):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # args = self.CHORDS_MAPPING[event.button.id]
        default_args = (2, 1 / 4, 1 / 8)

        if event.button.id.startswith("chord-"):
            chord = str(event.button.id).replace("chord-", "")
            chord = C(chord, *default_args) * 2
            play(chord, bpm=90, instrument=25)

        if event.button.id == "drumbeat":
            drum1 = drum("K, H, S, H, r:2, K, H, S, H, r:2")
            play(drum1, instrument=1)

        if event.button.id.startswith("drums-"):
            beat = event.button.id.replace("drums-", "")
            beat = drum(beat)
            play(beat, instrument=1)

        if event.button.id == "wholesong":
            chorus = (
                C('G', 2, 1)^2 |
                C('Bm', 2, 1)^2 |
                C('C', 2, 1)^2 |
                C('D', 2, 1)^2 |
                C('Em', 2, 1)^2 |
                C('Bm', 2, 1)^2 |
                C('Em', 2, 1/2)^2 |
                C('D', 2, 1/2)^2 |

                C('G', 2, 1)^2 |
                C('Bm', 2, 1)^2 |
                C('C', 2, 1)^2 |
                C('D', 2, 1)^2 |
                C('Em', 2, 1)^2 |
                C('D/F#', 2, 1)^2 |
                C('Am', 2, 1)^2 |
                C('Am', 2, 1)^2 |
                C('C', 2, 1)^2 |
                C('D', 2, 1)^2 |
                C('G', 2, 1)^2
            )
            # play(guitar, bpm=155, instrument=25, wait=True)

            drum1 = drum("K, H, S, H, r:2, K, H, S, H, r:2").notes * 7
            drum1.set_volume(112)

            result = piece(
                [chorus],
                [25, 1],
                bpm=145,
                start_times=[0, 0],
                channels=[0, 9],
            )
            play(result)

    def compose(self) -> ComposeResult:
        yield Grid(
            Button("F", id="chord-F", variant="success"),
            Button("C", id="chord-C", variant="success"),
            Button("Dm", id="chord-Dm", variant="success"),
            Button("Bb", id="chord-Bb", variant="success"),
            Button("Am", id="chord-Am", variant="success"),
            Button("Kick", id="drums-K", variant="success"),
            Button("Hi-hat", id="drums-H", variant="success"),
            Button("Snare", id="drums-S", variant="success"),
            Button("Open Hi-hat", id="drums-OH", variant="success"),
            Button("Pedal Hi-hat", id="drums-PH", variant="success"),
            Button("Drums", id="drumbeat", variant="success"),
            Button("Play", id="wholesong", variant="success"),
        )
