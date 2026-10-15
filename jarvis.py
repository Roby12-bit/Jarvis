import os
import json
import time
import subprocess
import webbrowser
import urllib.parse
import multiprocessing 
import speech_recognition as sr
from groq import Groq
import pyttsx3  # text-to-speech
import requests   # google api -> code
#import tkinter as tk 
#from datetime import datetime

# 1. CONFIGURARE DISPOZITIVE
INDEX_VOCE_ALEASA = 0 
LISTA_MICROFOANE = [None]  # Microfonul implicit din Windows

def _speak_worker(text, index_voce):
    """Proces izolat care execută sinteza vocală și eliberează imediat driverul SAPI5."""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 1.0)
        
        voices = engine.getProperty('voices')
        if index_voce < len(voices):
            engine.setProperty('voice', voices[index_voce].id)
            
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Error TTS Worker: {e}]")

def vorbeste(text):
    """Lansează o instanță separată de proces pentru fiecare replică vocală."""
    if not text:
        return
    p = multiprocessing.Process(target=_speak_worker, args=(text, INDEX_VOCE_ALEASA))
    p.start()
    p.join()  # Așteaptă finalizarea vorbirii înainte de a continua codul

# 2. AUTENTIFICAREA & MODELUL GROQ
client = Groq(api_key="...")
MODEL_NAME = "qwen/qwen3.8-27b"

# 3. FUNCȚIE SPEECH-TO-TEXT (MICROFON -> GROQ WHISPER)
def asculta_microfon():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 0.8
    
    audio = None

    for dev_index in LISTA_MICROFOANE:
        try:
            with sr.Microphone(device_index=dev_index) as source:
                microfon_folosit = dev_index if dev_index is not None else "Implicit (Default)"
                print(f"\n[Jarvis is listening on microphone {microfon_folosit}... speak now]")
                
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
                break

        except (OSError, Exception) as e:
            nume_mic = dev_index if dev_index is not None else "Implicit"
            print(f"[Microphone [{nume_mic}] not accessible. Trying next...]")
            continue

    if audio is None:
        print("[No speech detected or no microphone available.]")
        return ""

    try:
        print("[Audio processing with Whisper...]")
        wav_data = audio.get_wav_data()
        temp_filename = "temp_voice.wav"
        
        with open(temp_filename, "wb") as f:
            f.write(wav_data)

        with open(temp_filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(temp_filename, file.read()),
                model="whisper-large-v3-turbo",
                language="en" 
            )
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        text_transcris = transcription.text.strip()
        print(f"You (spoken): {text_transcris}")
        return text_transcris

    except Exception as e:
        print(f"[Error processing audio with Whisper: {e}]")
        return ""

# 4. FUNCȚII LOCALE
def deschide_in_browser(url, browser="default"):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    b = browser.lower().strip()
    browsere_protocol = {
        "edge": "msedge",
        "chrome": "chrome",
        "firefox": "firefox",
        "opera": "opera",
        "brave": "brave"
    }

    browser_exec = None
    for nume, comanda in browsere_protocol.items():
        if nume in b:
            browser_exec = comanda
            break

    if browser_exec:
        try:
            subprocess.Popen(f'start "" {browser_exec} "{url}"', shell=True)
            return f"in {browser}"
        except Exception:
            webbrowser.open(url)
            return "in default browser"
    else:
        webbrowser.open(url)
        return "in default browser"

def deschide_notepad():
    subprocess.Popen(["notepad.exe"])
    return "Opened Notepad."

def deschide_site_web(url, browser="default"):
    status = deschide_in_browser(url, browser)
    return f"Opened {url} {status}."

def cauta_pe_youtube(cautare: str, browser: str = "default"):
    query_encoded = urllib.parse.quote(cautare)
    url = f"https://www.youtube.com/results?search_query={query_encoded}"
    status = deschide_in_browser(url, browser)
    return f"Searched YouTube for '{cautare}' {status}."

def scrie_in_notepad(text: str, nume_fisier: str = "notita.txt"):
    try:
        with open(nume_fisier, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.Popen(["notepad.exe", nume_fisier])
        return f"Saved text to '{nume_fisier}' and opened Notepad."
    except Exception as e:
        return f"Error writing to file: {e}"

def deschide_aplicatie(nume_aplicatie: str):
    """Lansează o aplicație instalată în Windows pe baza numelui ei."""
    app = nume_aplicatie.lower().strip()
    
    comenzi = {
        "opera": "opera",
        "opera gx": "opera",
        "chrome": "chrome",
        "edge": "msedge",
        "firefox": "firefox",
        "brave": "brave",
        "calculator": "calc",
        "notepad": "notepad",
        "paint": "mspaint",
        "cmd": "cmd"
    }
    
    executabil = None
    for nume, cmd in comenzi.items():
        if nume in app:
            executabil = cmd
            break
            
    if not executabil:
        executabil = app
        
    try:
        subprocess.Popen(f'start "" {executabil}', shell=True)
        return f"Opened {nume_aplicatie}."
    except Exception as e:
        return f"Failed to open {nume_aplicatie}: {e}"

def descriere_actiune(func_name, func_args):
    """Mapează apelul de funcție la o descriere scurtă în engleză."""
    if func_name == "cauta_pe_youtube":
        return f"search YouTube for '{func_args.get('cautare', '')}'"
    elif func_name == "scrie_in_notepad":
        return "write text in Notepad"
    elif func_name == "deschide_notepad":
        return "open Notepad"
    elif func_name == "deschide_aplicatie":
        return f"open {func_args.get('nume_aplicatie', 'the app')}"
    elif func_name == "deschide_site_web":
        return f"open {func_args.get('url', 'the website')}"
    elif func_name == "afla_vremea":
        return f"check the weather for {func_args.get('oras', 'the city')}"
    return f"execute {func_name}"

def cere_confirmare(text_actiune):
    """Întreabă utilizatorul cu voce tare și ascultă AUTOMAT răspunsul."""
    intrebare = f"Did you mean to {text_actiune}? Please say yes or no."
    print(f"\nJarvis: {intrebare}")
    vorbeste(intrebare)
    
    time.sleep(0.3)
    
    intrare = asculta_microfon().lower()
    
    if not intrare:
        intrare = input("[Nu am auzit răspunsul. Scrie 'yes'/'no' sau apasă Enter pt reîncercare]: ").strip().lower()
        if not intrare:
            intrare = asculta_microfon().lower()
    
    afirmativ = ["yes", "yeah", "sure", "yep", "do it", "da", "correct"]
    if any(cuvant in intrare for cuvant in afirmativ):
        return True
    return False

def afla_vremea(oras: str, zile_prognoza: int = 0):
    """Obține vremea curentă sau prognoza pe mai multe zile folosind Open-Meteo."""
    try:
        # 1. Obținem coordonatele geografice exacte ale orașului (Geocoding)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={oras}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, headers={"User-Agent": "Jarvis/1.0"}).json()
        
        if not geo_res.get("results"):
            return f"Could not find coordinates for '{oras}'."
        
        locatie = geo_res["results"][0]
        lat, lon = locatie["latitude"], locatie["longitude"]
        nume_oras = locatie.get("name", oras)
        tara = locatie.get("country", "")

        # 2. Interogăm vremea pe baza coordonatelor
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        w_res = requests.get(weather_url, headers={"User-Agent": "Jarvis/1.0"}).json()

        curent = w_res.get("current_weather", {})
        temp_curenta = curent.get("temperature")

        # Dacă s-a cerut doar vremea de azi/curentă
        if zile_prognoza <= 0:
            return f"In {nume_oras} ({tara}), the current temperature is {temp_curenta}°C."

        # Dacă s-a cerut prognoza pe mai multe zile
        daily = w_res.get("daily", {})
        dates = daily.get("time", [])
        max_t = daily.get("temperature_2m_max", [])
        min_t = daily.get("temperature_2m_min", [])

        prognoza = [f"Current: {temp_curenta}°C."]
        limita = min(zile_prognoza + 1, len(dates))
        for i in range(1, limita):
            prognoza.append(f"Date {dates[i]}: Max {max_t[i]}°C, Min {min_t[i]}°C.")

        return f"Forecast for {nume_oras} ({tara}): " + " | ".join(prognoza)

    except Exception as e:
        return f"Error fetching weather data: {e}"

def trackBitcoin():
    """Fetches the current Bitcoin price in USD using CoinGecko API."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    headers = {"User-Agent": "Mozilla/5.0"}  # Previne blocarea de către CoinGecko
    try:
        raspuns = requests.get(url, headers=headers).json()
        pret_btc = raspuns.get("bitcoin", {}).get("usd")
        if pret_btc is not None:
            return f"The current price of Bitcoin is ${pret_btc:,} USD."
        else:
            return "Could not retrieve Bitcoin price."
    except Exception as e:
        return f"Error fetching Bitcoin price: {e}"
    
functii_locale = {
    "deschide_notepad": deschide_notepad,
    "deschide_site_web": deschide_site_web,
    "afla_vremea": afla_vremea,
    "trackBitcoin": trackBitcoin,
    "cauta_pe_youtube": cauta_pe_youtube,
    "scrie_in_notepad": scrie_in_notepad,
    "deschide_aplicatie": deschide_aplicatie,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "deschide_notepad",
            "description": "Opens Notepad.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deschide_site_web",
            "description": "Opens a website URL in a browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Exact URL or domain"},
                    "browser": {"type": "string", "description": "Browser name"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cauta_pe_youtube",
            "description": "Searches YouTube for videos or music.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cautare": {"type": "string", "description": "Search query"},
                    "browser": {"type": "string", "description": "Browser name"}
                },
                "required": ["cautare"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrie_in_notepad",
            "description": "Writes text into a file and opens Notepad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text content"},
                    "nume_fisier": {"type": "string", "description": "Filename"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deschide_aplicatie",
            "description": "Opens a Windows application or browser by name (e.g., Opera GX, Chrome, Calculator, Edge).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nume_aplicatie": {"type": "string", "description": "The name of the app to launch (e.g. Opera GX, Chrome, Calculator)"}
                },
                "required": ["nume_aplicatie"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "afla_vremea",
        "description": "Fetches current weather or multi-day forecast for a specified city.",
        "parameters": {
            "type": "object",
            "properties": {
                "oras": {
                    "type": "string", 
                    "description": "City name (e.g. Pitesti, Bucharest, London)"
                },
                "zile_prognoza": {
                    "type": "integer", 
                    "description": "Number of future forecast days requested (0 for current weather only, 1 to 5 for upcoming days)."
                }
            },
            "required": ["oras"]
        }
    }
},
    {
        "type": "function",
        "function": {
            "name": "trackBitcoin",
            "description": "Fetches the current live price of Bitcoin in USD.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

messages = [
    {
        "role": "system",
        "content": (
            "You are Jarvis, a personal virtual assistant. Respond concisely, politely, and directly in English (maximum 2 sentences).\n"
            "MANDATORY RULES:\n"
            "1. If the user asks to open an app or browser (like Opera GX, Chrome, Calculator), call `deschide_aplicatie`.\n"
            "2. If the user asks to write/note something in Notepad, ONLY call `scrie_in_notepad`.\n"
            "3. If searching YouTube, ONLY call `cauta_pe_youtube`.\n"
            "4. Keep responses concise as they will be spoken out loud."
            "5. If the user asks for Bitcoin price, ONLY call `trackBitcoin`."
            "6. If the user asks for weather, ONLY call `afla_vremea`."
            "7. If the user suggests opening a website regarding personal or sensitive information, politely refuse and do not call `deschide_site_web`."
            "8. If the user asks to check the weather at home, call `afla_vremea` with the city name 'Pitesti'."
        )
    }
]

# 5. EXECUȚIA PRINCIPALĂ
if __name__ == '__main__':
    print("Jarvis (Voice & Text Controlled) is online!\n")
    vorbeste("System online. Ready for commands.")

    while True:
        comanda_intrare = input("\n[Press Enter for Microphone | Write command / 'exit']: ").strip()

        if comanda_intrare.lower() in ['exit', 'quit']:
            mesaj = "System shutting down. Goodbye!"
            print(f"Jarvis: {mesaj}")
            vorbeste(mesaj)
            break

        if comanda_intrare:
            cerere = comanda_intrare
            e_comanda_vocala = False 
            print(f"You (written): {cerere}")
        else:
            cerere = asculta_microfon()
            e_comanda_vocala = True
            if not cerere:
                continue

        print("Jarvis: Processing...", end="", flush=True)
        messages.append({"role": "user", "content": cerere})

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=200
            )

            response_message = response.choices[0].message
            messages.append(response_message)

            if response_message.tool_calls:
                if e_comanda_vocala:
                    descrieri = []
                    for tool_call in response_message.tool_calls:
                        fn_name = tool_call.function.name
                        fn_args = json.loads(tool_call.function.arguments)
                        descrieri.append(descriere_actiune(fn_name, fn_args))
                    
                    text_sumar = " and ".join(descrieri)
                    
                    if not cere_confirmare(text_sumar):
                        mesaj_anulare = "Command cancelled. What else can I help you with?"
                        print(f"Jarvis: {mesaj_anulare}\n")
                        vorbeste(mesaj_anulare)
                        
                        messages.pop()
                        messages.pop()
                        continue

                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    if func_name in functii_locale:
                        rezultat = functii_locale[func_name](**func_args)
                        
                        if rezultat is None:
                            rezultat = "Action completed successfully."

                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": str(rezultat)
                        })

                second_response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    max_tokens=200
                )
                text_raspuns = second_response.choices[0].message.content
                print(f"\rJarvis: {text_raspuns}\n")
                messages.append(second_response.choices[0].message)
                vorbeste(text_raspuns)
            else:
                text_raspuns = response_message.content
                print(f"\rJarvis: {text_raspuns}\n")
                vorbeste(text_raspuns)

        except Exception as e:
            eroare_msg = "An error occurred while processing."
            print(f"\rJarvis: {eroare_msg} ({e})\n")
            vorbeste(eroare_msg)
