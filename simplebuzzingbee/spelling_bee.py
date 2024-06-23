def spelling_bee():
    import PySimpleGUI as sg
    from load_data import read_load_data
    import random
    import pyttsx3
    from gtts import gTTS
    from pygame import mixer
    import time

    sg.theme('Light Blue 7')  # Let's set our own color theme
    score=0
    count = -99
    word = ''
    part_of_speech = ''
    used_words = list()
    # STEP 1 define the layout_spelling
    layout_spelling = [
                [sg.Text('You are Playing Spelling Bee',font=('arial',18,'bold'),auto_size_text=True)],
                [sg.Text('Enter the number of words you would like to play:'),sg.InputText("",key='-IN0-'),sg.Button('Start') ],
                [sg.Text('Score'),sg.Text(score,key='-SCORE-') ],
                [sg.Button('Speak'),sg.Button('Part Of Speech'),sg.Button('Language Of Origin'),sg.Button('Definition'), ],
                [sg.Text('Part Of Speech :'),sg.Text('',key='-POS-') ],
                [sg.Text('Definition :'),sg.Text('',key='-DEFN-') ],
                [sg.Text('Language Of Origin :'),sg.Text('',key='-LOO-') ],
                [sg.InputText(key='-IN-'),sg.Button('Submit') ],
                [sg.Text('Correct Definition : '),sg.Text('',key='-CDEFN-',font=('arial',12,'italic'),auto_size_text=True),],
                [sg.Button('Previous'),sg.Button('Next'), ],
                [sg.Button('Back'),sg.Button('Exit')]
             ]

    #STEP 2 - create the window_spelling
    window_spelling = sg.Window('Spelling Bee Edventure!', layout_spelling)

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    # event, values = window_spelling.read()   # Read the event that happened and the values dictionary
    a,b,c = read_load_data()
    # STEP3 - the event loop
    while True:

        event, values = window_spelling.read()   # Read the event that happened and the values dictionary
        print(event, values)
        window_spelling['-IN-'].bind("<Return>", "_Enter")
        if count!=-99:
            word = c[a[count]].get('word', 'None')
            defn = c[a[count]].get('meaning', 'None')
            pos = c[a[count]].get('part_of_speech', 'None')
            loo = c[a[count]].get('origins', 'None')

        if event == sg.WIN_CLOSED or event == 'Exit':     # If user closed window_spelling with X or if user clicked "Exit" button then exit
          break
        if event == 'Back' or len(used_words) == len(a):
          break
        if event == 'Start':
            count=0
            a = random.choices(a, k=int(values.get('-IN0-', '10')))
            word = c[a[0]].get('word', 'None')
            defn = c[a[0]].get('meaning', 'None')
            pos = c[a[0]].get('part_of_speech', 'None')
            loo = c[a[0]].get('origins', 'None')
        if event == 'Speak':
            tts = gTTS(word)


            try:
                tts.save(word + '.mp3')
            except:
                print('file exists')
            mixer.init()
            mixer.music.load("{}.mp3".format(word))
            mixer.music.play()
            # time.sleep(10)
            # engine.say(word)
            # engine.runAndWait()
        if event == 'Definition':
            window_spelling['-DEFN-'].update(defn)
        if event == 'Part Of Speech':
            window_spelling['-POS-'].update(pos)
        if event == 'Language Of Origin':
            window_spelling['-LOO-'].update(loo)
        if event == 'Submit' or event == "-IN-_Enter":
            if values['-IN-'] == word and word not in used_words:
                score = score + 1
                window_spelling['-SCORE-'].update(score)
            used_words.append(word)
            window_spelling['-CDEFN-'].update(word.upper())
        if event == 'Previous':
          count = max(0,count-1)
          window_spelling['-CDEFN-'].update('')
          window_spelling['-DEFN-'].update('')
          window_spelling['-POS-'].update('')
          window_spelling['-LOO-'].update('')
          window_spelling['-IN-'].update('')
        if event == 'Next':
          count = min(len(a)-1,count+1)
          window_spelling['-CDEFN-'].update('')
          window_spelling['-DEFN-'].update('')
          window_spelling['-POS-'].update('')
          window_spelling['-LOO-'].update('')
          window_spelling['-IN-'].update('')

    window_spelling.close()
if __name__ == '__main__':
    spelling_bee()