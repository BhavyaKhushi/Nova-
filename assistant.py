import pyttsx3
import speech_recognition as sr
from datetime import date
import time
import webbrowser
import datetime
from pynput.keyboard import Key, Controller
import sys
import os
from os import listdir
from os.path import isfile, join
from threading import Thread
import app
from network_tracker import run_network_usage_tracker
import subprocess
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
import urllib.parse

# -------------Object Initialization---------------
today = date.today()
r = sr.Recognizer()
keyboard = Controller()
engine = pyttsx3.init('sapi5')
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# Audio Volume Control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_control = cast(interface, POINTER(IAudioEndpointVolume))

# ----------------Variables------------------------
file_exp_status = False
files = []
path = ''
is_awake = True

# ------------------Functions----------------------
def reply(audio):      # Converts the audio message to speech using pyttsx3
    app.ChatBot.addAppMsg(audio)
    print(audio)
    engine.say(audio)
    engine.runAndWait()

def wish():            # Greets the user based on the time of day
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        reply("Good Morning!")
    elif hour >= 12 and hour < 18:
        reply("Good Afternoon!")
    else:
        reply("Good Evening!")
    reply("I am Nova, how may I help you?")

def run_translator_gui():     # Launches the voice translator GUI
    try:
        print("Launching Voice Translator GUI...")
        import main
        main.run_translator()
        reply("Voice Translator closed.")
    except Exception as e:
        print(f"Error launching Translator: {str(e)}")
        reply("Sorry, there was an error while launching the Voice Translator.")


with sr.Microphone() as source:
    r.energy_threshold = 500
    r.dynamic_energy_threshold = False

def record_audio():         # Records audio from the microphone and converts it to text
    with sr.Microphone() as source:
        r.pause_threshold = 0.8
        voice_data = ''
        audio = r.listen(source, phrase_time_limit=5)
        try:
            voice_data = r.recognize_google(audio)
        except sr.RequestError:
            reply('Sorry my service is down. Please check your internet connection.')
        except sr.UnknownValueError:
            print('Cannot recognize')
        return voice_data.lower()

# New: Volume Control
def change_volume(up=True):      # Increases or decreases the system volume by 10%
    current_volume = volume_control.GetMasterVolumeLevelScalar()
    step = 0.1
    new_volume = current_volume + step if up else current_volume - step
    new_volume = max(0.0, min(1.0, new_volume))
    volume_control.SetMasterVolumeLevelScalar(new_volume, None)
    reply(f"Volume {'increased' if up else 'decreased'}")


# New: Open Windows Settings 
def open_settings_page(setting):  # Opens a specific Windows settings page
    try:
        subprocess.run(["start", f"ms-settings:{setting}"], shell=True)
        reply(f"Opening {setting.replace('-', ' ')} settings.")
    except Exception as e:
        reply(f"Failed to open {setting} settings.")

import subprocess

# Function to open applications based on the user's command
def open_application(app_name):
    try:
        if app_name == 'notepad':
            subprocess.Popen('notepad.exe')
            reply("Opening Notepad...")
        elif app_name == 'calculator':
            subprocess.Popen('calc.exe')
            reply("Opening Calculator...")
        elif app_name == 'word':
            word_path = r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"
            if os.path.exists(word_path):
                   subprocess.Popen(word_path)
                   reply("Opening Microsoft Word...")
            else:
                   reply("Microsoft Word not found. Please check the installation path.")
        elif app_name == 'excel':
            excel_path = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
            if os.path.exists(excel_path):
                subprocess.Popen(excel_path)
                reply("Opening Microsoft Excel...")
            else:
                reply("Microsoft Excel not found. Please check the path.")

        elif app_name == 'powerpoint':
            ppt_path = r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"
            if os.path.exists(ppt_path):
                subprocess.Popen(ppt_path)
                reply("Opening Microsoft PowerPoint...")
            else:
                reply("Microsoft PowerPoint not found. Please check the path.")

        elif app_name == 'chrome':    
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if os.path.exists(chrome_path):
                   subprocess.Popen(chrome_path)
                else:
                    print("Chrome not found at the default location.")
        
        else:
            reply(f"Sorry, I can't open {app_name} yet.")
    except Exception as e:
        reply(f"Error opening {app_name}: {str(e)}")

def play_youtube_video(query):
    search_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={search_query}"
    webbrowser.open(url)
    reply(f"Searching YouTube for {query}")

def respond(voice_data):      #  Processes voice commands and performs actions
    global file_exp_status, files, is_awake, path
    print(voice_data)
    voice_data = voice_data.lower().replace('nova', '')  # Ensure voice_data is properly sanitized
    app.eel.addUserMsg(voice_data)

    if not is_awake:
        if 'wake up' in voice_data:
            is_awake = True
            wish()
        return

    # STATIC CONTROLS
    if 'hello' in voice_data:
        wish()

    elif 'what is your name' in voice_data:
        reply('My name is nova!')

    elif 'date' in voice_data:
        reply(today.strftime("%B %d, %Y"))

    elif 'time' in voice_data:
        reply(str(datetime.datetime.now()).split(" ")[1].split('.')[0])

    elif 'search' in voice_data:
        reply('Searching for ' + voice_data.split('search')[1])
        url = 'https://google.com/search?q=' + voice_data.split('search')[1]
        try:
            webbrowser.get().open(url)
            reply('This is what I found')
        except:
            reply('Please check your Internet Connection')

    elif 'location' in voice_data:
        reply('Which place are you looking for?')
        temp_audio = record_audio()
        app.eel.addUserMsg(temp_audio)
        reply('Locating...')
        url = 'https://google.nl/maps/place/' + temp_audio + '/&amp;'
        try:
            webbrowser.get().open(url)
            reply('This is what I found')
        except:
            reply('Please check your Internet Connection')

    elif 'goodbye' in voice_data or 'bye' in voice_data or 'by' in voice_data:
        reply("Goodbye! Have a nice day.")
        try:
            app.ChatBot.closeApp()  # Call your GUI cleanup if it exists
        except Exception as e:
            print(f"Error closing GUI: {e}")
        sys.exit(0)  # Exit cleanly

    # SYSTEM SETTINGS CONTROLS
    elif 'increase volume' in voice_data:
        change_volume(up=True)

    elif 'decrease volume' in voice_data:
        change_volume(up=False)

    elif 'open hotspot' in voice_data:
        open_settings_page("network-mobilehotspot")

    elif 'open airplane mode' in voice_data or 'airplane mode' in voice_data:
        open_settings_page("network-airplanemode")

    # DYNAMIC CONTROLS
    elif 'launch translator' in voice_data or 'open translator' in voice_data:
        reply('Launching Voice Translator...')
        t2 = Thread(target=run_translator_gui)
        t2.start()

    elif 'open network usage' in voice_data or 'network usage' in voice_data:
        reply('Opening Network Usage Tracker...')
        t3 = Thread(target=run_network_usage_tracker)
        t3.start()

    elif 'copy' in voice_data:
        with keyboard.pressed(Key.ctrl):
            keyboard.press('c')
            keyboard.release('c')
        reply('Copied')

    elif 'paste' in voice_data or 'pest' in voice_data or 'page' in voice_data:
        with keyboard.pressed(Key.ctrl):
            keyboard.press('v')
            keyboard.release('v')
        reply('Pasted')

    elif 'list' in voice_data:
        counter = 0
        path = 'C://'
        files = listdir(path)
        filestr = ""
        for f in files:
            counter += 1
            print(str(counter) + ':  ' + f)
            filestr += str(counter) + ':  ' + f + '<br>'
        file_exp_status = True
        reply('These are the files in your root directory')
        app.ChatBot.addAppMsg(filestr)

    elif file_exp_status:
        counter = 0
        if 'open' in voice_data:
            index = int(voice_data.split(' ')[-1]) - 1
            if isfile(join(path, files[index])):
                os.startfile(path + files[index])
                file_exp_status = False
            else:
                try:
                    path += files[index] + '//'
                    files = listdir(path)
                    filestr = ""
                    for f in files:
                        counter += 1
                        filestr += str(counter) + ':  ' + f + '<br>'
                        print(str(counter) + ':  ' + f)
                    reply('Opened Successfully')
                    app.ChatBot.addAppMsg(filestr)
                except:
                    reply('You do not have permission to access this folder')

        elif 'back' in voice_data:
            filestr = ""
            if path == 'C://':
                reply('Sorry, this is the root directory')
            else:
                path = '//'.join(path.split('//')[:-2]) + '//'
                files = listdir(path)
                for f in files:
                    counter += 1
                    filestr += str(counter) + ':  ' + f + '<br>'
                    print(str(counter) + ':  ' + f)
                reply('ok')
                app.ChatBot.addAppMsg(filestr)
    # OPEN APPLICATIONS BY VOICE
    elif 'open notepad' in voice_data or 'launch notepad' in voice_data:
        open_application('notepad')

    elif 'open calculator' in voice_data or 'launch calculator' in voice_data:
        open_application('calculator')

    elif 'open microsoft word' in voice_data or 'launch microsoft word' in voice_data:
        open_application('word')

    elif 'open excel' in voice_data or 'launch excel' in voice_data:
        open_application('excel')
    
    elif 'open powerpoint' in voice_data or 'launch powerpoint' in voice_data:
        open_application('powerpoint')
    
    elif 'open chrome' in voice_data or 'launch chrome' in voice_data:
        open_application('chrome')

    #play youtube video
    elif 'play' in voice_data and 'youtube' in voice_data:
        try:
            video_query = voice_data.replace('play', '').replace('on youtube', '').replace('youtube', '').strip()
            if video_query:
                play_youtube_video(video_query)
            else:
                reply("Please tell me what you want to play on YouTube.")
        except Exception as e:
            reply("Sorry, something went wrong while opening YouTube.")
            print(f"Error: {e}")


    else:
        reply('I am not functioned to do this!')

    

# ------------------Driver Code--------------------
t1 = Thread(target=app.ChatBot.start)
t1.start()

while not app.ChatBot.started:
    time.sleep(0.5)

wish()
voice_data = None
while True:       # The main loop continuously listens for user input
    if app.ChatBot.isUserInput():
        voice_data = app.ChatBot.popUserInput()
    else:
        voice_data = record_audio()

    if 'nova' in voice_data:
        try:
            respond(voice_data)
        except SystemExit:
            reply("Exit Successful")
            break
        except:
            print("Exception raised while closing.")
            break