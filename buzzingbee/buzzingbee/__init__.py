from __future__ import annotations

from pathlib import Path
from typing import *  # type: ignore

import rio

from . import pages
from . import components as comps

# Define a theme for Rio to use.
#
# You can modify the colors here to adapt the appearance of your app or website.
# The most important parameters are listed, but more are available! You can find
# them all in the docs
#
# https://rio.dev/docs/api/theme
theme = rio.Theme.from_colors(
    primary_color=rio.Color.from_hex("01dffdff"),
    secondary_color=rio.Color.from_hex("0083ffff"),
    mode="light",
)


# Create the Rio app
app = rio.App(
    name='buzzingbee',
    pages=[
        rio.Page(
            name="Home",
            page_url='',
            build=pages.HomePage,
        ),

        rio.Page(
            name="AboutPage",
            page_url='about-page',
            build=pages.AboutPage,
        ),

        rio.Page(
            name="SpellingBeePage",
            page_url='spelling-bee-page',
            build=pages.SpellingBeePage,
        ),

        rio.Page(
            name="VocabularyBeePage",
            page_url='vocabulary-bee-page',
            build=pages.VocabularyBeePage,
        ),
    ],
    # You can optionally provide a root component for the app. By default,
    # a simple `rio.PageView` is used. By providing your own component, you
    # can create components which stay put while the user navigates between
    # pages, such as a navigation bar or footer.
    #
    # When you do this, make sure your component contains a `rio.PageView`
    # so the currently active page is still visible.
    build=pages.RootPage,
    theme=theme,
    assets_dir=Path(__file__).parent / "assets",
)

