import pyttsx3
import datetime
import time
import webbrowser
import cv2
import torch
import numpy as np
import speech_recognition as sr
from googleapiclient.discovery import build
from google.oauth2 import service_account

def initialize_engine():
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume+0.25)
    return engine

def speak(text):
    engine = initialize_engine()
    engine.say(text)
    engine.runAndWait()

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("I'm listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio).lower()
            return command
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please try again.")
            return recognize_speech()
        except sr.RequestError:
            speak("Sorry, my speech service is unavailable right now.")
            return ""

def cal_day():
    day = datetime.datetime.today().weekday() + 1 
    day_dict={
        1:"Monday",
        2:"Tuesday",
        3:"Wednesday",
        4:"Thursday",
        5:"Friday",
        6:"Saturday",
        7:"Sunday"
    }
    return day_dict.get(day, "Unknown Day")

def wishMe():
    hour = int(datetime.datetime.now().hour)
    t = time.strftime("%I:%M %p")
    day = cal_day()
    speak(f"Sup Jayden, it's {day} and the time is {t}. Here's everything that happened today:")
    get_appointments()

def open_website(command):
    website_dict = {
        "facebook": "facebook.com",
        "instagram": "instagram.com",
        "twitter": "twitter.com",
        "youtube": "youtube.com",
        "google": "google.com",
        "reddit": "reddit.com",
        "github": "github.com",
        "school": "calendar.google.com"
    }
    words = command.split()
    for word in words:
        if word.lower() in website_dict:
            url = f"https://{website_dict[word.lower()]}"
            speak(f"Opening {word}")
            webbrowser.open(url)
            return
        elif any(ext in word for ext in [".com", ".org", ".net", ".io"]):
            url = f"https://{word}" if not word.startswith("http") else word
            speak(f"Opening {word}")
            webbrowser.open(url)
            return
    speak("Please specify a valid website.")

def get_appointments():
    try:
        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        SERVICE_ACCOUNT_FILE = "credentials.json"
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("calendar", "v3", credentials=credentials)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        end_of_day = (datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary", timeMin=now, timeMax=end_of_day, maxResults=50,
            singleEvents=True, orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        if not events:
            speak("You had no events scheduled for today.")
        else:
            speak("Here is what happened today:")
            for event in events:
                event_summary = event["summary"]
                start = event["start"].get("dateTime", event["start"].get("date"))
                start_time = datetime.datetime.fromisoformat(start[:-1]).strftime("%I:%M %p") if "T" in start else start
                speak(f"{event_summary} at {start_time}")
    except Exception as e:
        speak("I couldn't retrieve your calendar events. Please check your credentials.")

def detect_objects():
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        detected_objects = results.pandas().xyxy[0]['name'].unique()
        if len(detected_objects) > 0:
            speak(f"I see {', '.join(detected_objects)}")
        cv2.imshow('YOLOv5 Object Detection', np.squeeze(results.render()))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    wishMe()
    while True:
        speak("Would you like to open a website or detect objects?")
        choice = recognize_speech()
        print (choice)
        if "one" in choice:
            speak("Which website would you like to open?")
            query = recognize_speech()
            open_website(query)
        elif "two" in choice:
            detect_objects()
        else:
            speak("Invalid choice. Please say 'open web' or 'detect'.")