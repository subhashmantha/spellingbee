from shiny import App, ui

app_spell_ui = ui.page_fillable(
        ui.card(),
        ui.layout_column_wrap(
        ui.card(ui.input_numeric('wordcount',"Numeric input",1,min=1,max=1000),ui.input_action_button("spbtn","Say the word")),
        ui.card(
        ui.output_text_verbatim("text")) ,
        ui.card(
        ui.input_action_button("btndef", "Definition") ,
        ui.input_action_button("btnPOS", "Part of Speech"),
        ui.input_action_button("btnloo", "Language of Origin"),
        ),
        ui.card(
             ui.output_text_verbatim("Language_of_Origin"),
             ui.output_text_verbatim("Definition"),
             ui.output_text_verbatim("Part_of_Speech"),
        ),
        ui.card(),
        ),
)


def shinyspellbee_server(input, output, session):
    pass


