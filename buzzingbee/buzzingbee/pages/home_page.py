from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps

class HomePage(rio.Component):
    """
    A sample page, containing a greeting and some testimonials.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Markdown(
                """
# Buzzwordz Inc.!

Get on an edventerous ride to build your spelling power and vocabulary.
            """,
                width=60,
                align_x=0.5,
            ),
            rio.Link(rio.Row(
                rio.Button(
                    "Spelling Bee!",
                    on_press=lambda: print("Button pressed!"),
                ),
                align_x=0.5,
            ),'/spelling-bee-page'),
            rio.Link(rio.Row(
                rio.Button(
                    "Vocabulary Bee!",
                    on_press=lambda: print("Button pressed!"),
                ),
                align_x=0.5,
            ),'/vocabulary-bee-page'),
            rio.Row(
                rio.Button(
                    "Quit Playing",
                    on_press=lambda: print("Button pressed!"),
                ),
                align_x=0.5,
            ),
            rio.Markdown(
                """
Contact us today to unlock your word potential.
            """,
                width=60,
                align_x=0.5,
            ),
            spacing=2,
            width=60,
            align_x=0.5,
            align_y=0,
        )

