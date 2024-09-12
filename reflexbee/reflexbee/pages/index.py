"""The main index page."""

import reflex as rx



def index():
    return rx.center(rx.flex(
        rx.card(
            rx.box(
                rx.heading("Spelling and Vocabulary Edventures!"),
                rx.text("Welcome to an edventurous journey where you will learn spelling and improve vocabulary by playing different games."),
            )

            ,size="5"),
        rx.button("Spelling Bee !",
                  size='4',
                  color_scheme="yellow",
                  on_click=rx.redirect(
                      "/spellbee"
                  )
        ),
        rx.button("Vocabulary Bee !",
                  size='4',
                  color_scheme="blue",
                  on_click=rx.redirect(
                      "/vocabbee"
                  )
                  ),
        rx.button("Vocabulary Bee Alternate!",
                  size='4',
                  color_scheme="teal",
                  on_click=rx.redirect(
                      "/altvocabbee"
                  )
                  ),
        spacing = "2",
        direction = "column",


    ))

if __name__ == "__main__":
    app = rx.App()
    app.add_page(index)