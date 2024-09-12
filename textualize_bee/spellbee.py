from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header, Static, Placeholder, Input, TextArea, Label
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual import events, on
from textual.screen import Screen


class Header(Placeholder):
    DEFAULT_CSS = """
    Header {
        height: 6;
        dock: top;
    }
    """


class Footer(Placeholder):
    DEFAULT_CSS = """
    Footer {
        height: 6;
        dock: bottom;
    }
    """
class PlaySpellBee(Screen):
    CSS_PATH = "spellingbee.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Header(id="SpellBeeApp") 
        yield Input(placeholder="Enter number of words to play", id="wordcount")
        yield Button("Submit", id="submit")
        yield Label("Score",id="score")
        yield Button("Speak", id="speak")
        yield Button("Definition        ", id="defn")
        yield Label("Definition Text",id="defntext")
        yield Button("Part Of Speech    ", id="pos")
        yield Label("Part Of Speech Text", id="postext")
        yield Button("Language of Origin", id="loo")
        yield Label("Language of Origin", id="lootext")
        yield Input(placeholder="Enter Correct Spelling",id="correctspell")
        yield Button("Answer", id="answer")
        yield Button("Next", id="next")
        yield Button("Previous", id="previous")
        yield Button("Exit", id="exit")
        yield Footer(id="About")





