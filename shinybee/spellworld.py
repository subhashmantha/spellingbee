from shiny import App, ui, reactive
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from shinyspellbee import app_spell_ui, shinyspellbee_server

app_static = StaticFiles(directory=".")

app_ui = ui.page_fillable(
        ui.card(),
        ui.layout_column_wrap(
        ui.card(),
        ui.card(
        ui.input_action_button("btns", "Spelling Bee") ,
        ui.input_action_button("btnv", "Vocabulary Bee") ,
        ui.input_action_button("btnav", "Alternate Vocabulary Bee"),
        ),
        ui.card(),
        ),
)


def app_server(input, output, session):
    @reactive.effect
    def _():
        btn = input.btns()
        if btn == 1:
            return page_spell

    pass


page_home = App(ui=app_ui,server=app_server)
page_spell = App(ui=app_spell_ui,server=shinyspellbee_server)

routes = [
    Mount('/static', app=page_home),
    Mount('/spellbe', app=page_spell)
]






app = Starlette(routes=routes)