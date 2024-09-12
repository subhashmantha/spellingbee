

from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header, Static, Placeholder, Input, TextArea, Label, RadioButton, RadioSet
from textual.containers import ScrollableContainer, Horizontal, Vertical, VerticalScroll
from textual import events, on
from textual.screen import Screen

class PlayVocabBee(Screen):
    CSS_PATH = "vocabbee.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Header(id="ChampionsApp")
        yield Footer(id="About")
        yield Horizontal(Input(placeholder="Enter number of words to play", id="wordcount"),Button("Submit", id="submit1"))
        yield Horizontal(Label("Score",id="score"))
        yield Horizontal(Label("Word",id="word"),Button("Speak", id="speak"))


        with RadioSet(id="focus_me"):
            yield RadioButton("Text 1",id="text1")
            yield RadioButton("Text 2", id="text2")
            yield RadioButton("Text 3", id="text3")
            yield RadioButton("Text 4", id="text4")

        yield Horizontal(Button("Next", id="next"), Button("Previous", id="previous"),  Button("Exit", id="exit"))




