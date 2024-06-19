def vocabulary_bee():
    import PySimpleGUI as sg
    from load_data import read_load_data
    import random
    import pyttsx3

    sg.theme('Green Mono')  # Let's set our own color theme
    score=0
    count = 0
    count_prv = -1
    count_nxt = 1000
    word = ''
    part_of_speech = ''
    word1 = ''
    word2 = ''
    word3 = ''
    word4 = ''
    used_words = list()
    # STEP 1 define the layout_vocab
    layout_vocab = [
                [sg.Text('You are Playing Vocabulary Bee',font=('arial',18,'bold'),auto_size_text=True)],
                [sg.Text('Enter the number of words you would like to play:'),sg.InputText(key='-IN0-'),sg.Button('Start') ],
                [sg.Text('Score :'),sg.Text(score,key='-SCORE-') ],
                [sg.Text(word,key='-WORD-',font=('arial',12,'bold'),auto_size_text=True),sg.Text('::'),sg.Text(part_of_speech,key='-POS-',font=('arial',12,'italic'),auto_size_text=True),sg.Button('Speak') ],
                [sg.Radio('', group_id=1),sg.Text(word1,key='-WORD1-',font=('arial',12),auto_size_text=True), ],
                [sg.Radio('', group_id=1),sg.Text(word2,key='-WORD2-',font=('arial',12),auto_size_text=True), ],
                [sg.Radio('', group_id=1),sg.Text(word3,key='-WORD3-',font=('arial',12),auto_size_text=True),],
                [sg.Radio('', group_id=1),sg.Text(word4,key='-WORD4-',font=('arial',12),auto_size_text=True),],
                [sg.Text('Correct Definition : '),sg.Text('',key='-CDEFN-',font=('arial',12,'italic'),auto_size_text=True),],
                [sg.Button('Submit'),],
                [sg.Button('Previous'),sg.Button('Next'),sg.Button('Back') ],
                [sg.Button('Exit')]
             ]

    #STEP 2 - create the window_vocab
    window_vocab = sg.Window('Vocabulary Bee Edventure!', layout_vocab,resizable=True)
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    # event, values = window_vocab.read()   # Read the event that happened and the values dictionary
    a,b,c = read_load_data()
    # STEP3 - the event loop
    while True:
        event,values = window_vocab.read()
        if event == sg.WIN_CLOSED or event == 'Exit' or event == 'Back':     # If user closed window_vocab with X or if user clicked "Exit" button then exit
          break
        if event == 'Start':
            a = random.choices(a,k=int(values.get('-IN0-','10')))
            word = c[a[count]].get('word', 'None')
            defn = c[a[count]].get('meaning', 'None')
            pos = c[a[count]].get('part_of_speech', 'None')
            other_choices = random.choices(b, k=3)
            other_choices.append(defn)
            random.shuffle(other_choices)
            word1, word2, word3, word4 = other_choices
            window_vocab['-WORD-'].update(word.upper())
            window_vocab['-WORD1-'].update(word1)
            window_vocab['-WORD2-'].update(word2)
            window_vocab['-WORD3-'].update(word3)
            window_vocab['-WORD4-'].update(word4)
            window_vocab['-POS-'].update(pos)
        if event == 'Speak':
          engine.say(word)
          engine.runAndWait()
        elif event == 'Submit':
          s = other_choices.index(defn)
          if values[s] == True and  word not in used_words:
           score=score+1
           window_vocab['-SCORE-'].update(str(score))
          window_vocab['-CDEFN-'].update(defn)
          used_words.append(word)
          # print('You pressed the Submit button')
        elif event == 'Previous':
          s = other_choices.index(defn)
          window_vocab[s].update(False)
          count=max(0,count-1)
          word = c[a[count]].get('word', 'None')
          defn = c[a[count]].get('meaning', 'None')
          pos = c[a[count]].get('part_of_speech', 'None')
          other_choices = random.choices(b, k=3)
          other_choices.append(defn)
          random.shuffle(other_choices)
          word1, word2, word3, word4 = other_choices
          window_vocab['-WORD-'].update(word.upper())
          window_vocab['-WORD1-'].update(word1)
          window_vocab['-WORD2-'].update(word2)
          window_vocab['-WORD3-'].update(word3)
          window_vocab['-WORD4-'].update(word4)
          window_vocab['-POS-'].update(pos)
          window_vocab['-CDEFN-'].update('')
        elif event == 'Next':
          count=min(int(values.get('-IN0-'))-1,count+1)
          s = other_choices.index(defn)
          window_vocab[s].update(False)
          word = c[a[count]].get('word', 'None')
          defn = c[a[count]].get('meaning', 'None')
          pos = c[a[count]].get('part_of_speech', 'None')
          other_choices = random.choices(b, k=3)
          other_choices.append(defn)
          random.shuffle(other_choices)
          word1, word2, word3, word4 = other_choices
          window_vocab['-WORD-'].update(word.upper())
          window_vocab['-WORD1-'].update(word1)
          window_vocab['-WORD2-'].update(word2)
          window_vocab['-WORD3-'].update(word3)
          window_vocab['-WORD4-'].update(word4)
          window_vocab['-POS-'].update(pos)
          window_vocab['-CDEFN-'].update('')
        elif event == 'Back' or count == int(values.get('-IN0-'))-1:
          break
    window_vocab.close()
if __name__ == '__main__':
    vocabulary_bee()
