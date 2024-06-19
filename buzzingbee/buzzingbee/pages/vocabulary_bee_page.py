from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps

class VocabularyBeePage(rio.Component):
    """
    A sample page, containing recent news articles about the company.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("Vocabulary Bee", style="heading1"),
            rio.Row(rio.Column(rio.Text("Score :", style="heading3")),rio.Column(rio.Text("0", style="heading3"),)),
            comps.VocabularyBee(
                "Disruptive Innovations Inc. is the vanguard of operational excellence and groundbreaking innovation.",
                "Jane Doe",
                "CTO, Synergistic Solutions LLC",

            ),
            rio.Row(
                rio.Button( "Previous",
                    on_press=lambda: print("Button pressed!"),),
                rio.Button( "Next",
                    on_press=lambda: print("Button pressed!"),),
            ),
            rio.Row(
                rio.Button("Back",
                           on_press=lambda: print("Button pressed!"), ),
                rio.Button("Quit",
                           on_press=lambda: print("Button pressed!"), ),
            ),
            spacing=2,
            width=60,
            margin_bottom=4,
            align_x=0.5,
            align_y=0,
        )

