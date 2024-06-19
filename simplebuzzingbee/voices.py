import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
index = 0
for voice in voices:
   print(f'index-> {index} -- {voice.name}')
   engine.setProperty('voice', voices[index].id)
   engine.say("hello I am the voice from your PC")
   index +=1
engine.runAndWait()