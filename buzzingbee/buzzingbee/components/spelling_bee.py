from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps

class SpellingBee(rio.Component):
    """
    Displays a news article with some visual separation from the background.
    """

    markdown: str

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Markdown(
                self.markdown,
                margin=2,
            )
        )

