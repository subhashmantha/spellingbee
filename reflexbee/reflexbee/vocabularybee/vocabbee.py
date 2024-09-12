import reflex as rx
@rx.page(route="/vocabbee", title="VocabularyBee")
def vocabbee():
    return rx.text("Vocab Bee Language")