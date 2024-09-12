import reflex as rx
import pandas as pd

class QuizState(rx.State):

    # The current question being asked.
    all_input: list
    question: str
    score: int
    total_questions: int
    loo: str
    pos: str
    disp_answer: str
    count_of_question: int
    how_many_questions_to_play: int
    list_of_words: list
    list_of_definitions: list
    input_num: int = 0
    # Keep track of the chat history as a list of (question, answer) tuples.

def load_data():
    import os
    import random
    pdf = pd.read_csv("{}/reflexbee/clean_dictionary_pipe.csv".format(os.getcwd()), delimiter='|')
    dict1 = pdf.to_dict('index')
    list_of_definitions = pdf.meaning.values
    list_of_words = pdf.word.values
    list_of_pos = pdf.part_of_speech.values
    list_of_origins = pdf.origins.values
    # word | origins | part_of_speech | pronunciation | meaning
    all_input = list(zip(list_of_words,list_of_definitions,list_of_pos,list_of_origins))
    QuizState.all_input = random.choices(all_input, k=int(QuizState.input_num.to_string()))
    QuizState.list_of_definitions = list_of_definitions
    QuizState.list_of_words = list_of_words
    s= QuizState.input_num
    print(s)



# if __name__ == '__main__':
#     a,b,c = load_data()
#     print(a[10])