import pandas as pd
import random

def read_load_data(file_name="clean_dictionary_pipe.csv"):

    pdf = pd.read_csv(file_name,delimiter='|')
    dict1 = pdf.to_dict('index')

    list_of_words = list(dict1.keys())
    list_of_definitions = pdf.meaning.values

    return (list_of_words,list_of_definitions,dict1)

if __name__ == '__main__':

    a,b,c = read_load_data()
    w = random.choices(a,k=10)
    print(a[0:5])
    print(b[0:5])
    for choice in w:
        print(c[choice])