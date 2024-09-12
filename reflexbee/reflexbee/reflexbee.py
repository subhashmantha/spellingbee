"""The main Dashboard App."""

from rxconfig import config

import reflex as rx

from reflexbee.styles import BACKGROUND_COLOR, FONT_FAMILY, THEME, STYLESHEETS


from reflexbee.pages.index import index
from reflexbee.spellingbee.spellbee import spellbee
from reflexbee.vocabularybee.vocabbee import vocabbee
from reflexbee.altvocabularybee.altvocabbee import altvocabbee

# Create app instance and add index page.
app = rx.App(
    theme=THEME,
    stylesheets=STYLESHEETS,
)

app.add_page(index, route="/")
app.add_page(spellbee, route="/spellbee")
app.add_page(vocabbee, route="/vocabbee")
app.add_page(altvocabbee, route="/altvocabbee")
