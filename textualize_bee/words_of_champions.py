from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header, Static, Placeholder, Input, Label
from textual.containers import ScrollableContainer, Horizontal, VerticalScroll
from textual import events, on
from textual.screen import Screen
#
# from play import Play
from spellbee import PlaySpellBee
from vocabbee import PlayVocabBee
from altvocabbee import PlayAltVocabBee

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


class Play(Screen):
   def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""

        yield Button("Spelling Bee", id="spellingbees")
        yield Button("Vocabulary Bee", id="vocabbees")
        yield Button("Alternate Vocabulary Bee", id="altvocabbees")



class ChampionsApp(App):
    """A Textual app to manage stopwatches."""
    CSS_PATH = "champions.tcss"

    SCREENS = {
        "spellbee": PlaySpellBee,
        "vocabbee": PlayVocabBee,
        "altvocabbee": PlayAltVocabBee,
    }

    # SCREENS = {"playbee": Play()}
    @on(Button.Pressed, "#spellingbees")
    def pressed_spellingbee(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        self.push_screen("spellbee")

    @on(Button.Pressed, "#vocabbees")
    def pressed_vocabbee(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        self.push_screen("vocabbee")

    @on(Button.Pressed, "#altvocabbees")
    def pressed_altvocabbee(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        self.push_screen("altvocabbee")

    @on(Button.Pressed, "#exit")
    def pressed_exit(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        self.pop_screen()

    def compose(self) -> ComposeResult:
        # self.switch_screen("playbee")
        yield Header(id="ChampionsApp")
        yield Footer(id="About")
        yield Play()







if __name__ == "__main__":
    app = ChampionsApp()
    app.run()