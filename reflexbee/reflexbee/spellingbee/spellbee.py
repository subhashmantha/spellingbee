import reflex as rx
import random
import pyttsx3
from gtts import gTTS
from pygame import mixer
from .state import QuizState,load_data

def qa(question: str, pos: str, loo:str) -> rx.Component:
    count = 0

    return rx.center(rx.flex(
        rx.hstack(
            rx.input(id='question_num', placeholder="How many questions you want to play...",
                     type="int", max_length=100,size="3"),
            rx.button("play", size='4',on_click=load_data())
        ),
      rx.box(
            rx.button("Speak", size="4")
            , size="5"
        ),
        rx.box(
            rx.text(pos, text_align="left")
            , size="5"
        ),
        rx.box(
            rx.text(loo, text_align="left")
            , size="5"
            ),
        rx.hstack(
            rx.input(id='response',placeholder="Enter Answer here...", max_length=100,size="3"),
            rx.button("submit",size='4')
        ),
       spacing = "6",
        direction = "column",
),
    spacing = "5")

@rx.page(route="/spellbee", title="SpellingBee")
def spellbee():
    return rx.box(qa("a","b","c"))