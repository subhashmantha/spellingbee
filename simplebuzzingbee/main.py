import PySimpleGUI as sg
from spelling_bee import spelling_bee
from vocabulary_bee import vocabulary_bee
from vocabulary_bee_v2 import vocabulary_bee_v2
sg.theme('Light Grey 4')  # Let's set our own color theme

# STEP 1 define the layout
layout = [
            [sg.Text('Build your vocabulary',font=('arial',18,'bold'),auto_size_text=True)],
            [sg.Button('Spelling Bee!'), ],
            [sg.Button('Vocabulary Bee!'), ],
            [sg.Button('Vocabulary Bee alternate version!'), ],
            [sg.Button('Exit')]
         ]

#STEP 2 - create the window
window = sg.Window('Word Power Edventure!', layout)

# STEP3 - the event loop
while True:
    event, values = window.read()   # Read the event that happened and the values dictionary
    print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':     # If user closed window with X or if user clicked "Exit" button then exit
      break
    if event == 'Spelling Bee!':
      print('You pressed the Spelling Bee button')
      spelling_bee()
    if event == 'Vocabulary Bee!':
      print('You pressed the Vocabulary Bee button')
      vocabulary_bee()
    if event == 'Vocabulary Bee alternate version!':
      print('You pressed the Vocabulary Bee button')
      vocabulary_bee_v2()
window.close()