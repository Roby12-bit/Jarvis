# Jarvis AI — Voice & Vision Desktop Assistant

**Jarvis** este un asistent virtual modular dezvoltat în Python, capabil să proceseze comenzi vocale și scrise, să execute acțiuni automate pe ecranul calculatorului prin OCR (Vision) și să interacționeze cu servicii externe prin API-uri în timp real.

Proiectul folosește **Groq API (Qwen 27B)** pentru raționament și înțelegerea limbajului natural, **Whisper** pentru recunoaștere vocală și un sistem hibrid de executare a acțiunilor prin *Function Calling*.

---

## Capabilități Principale

- **Control Vocal & Text:** Conversație fluidă prin microfon (Whisper Large v3) sau introducere de comenzi din tastatură.
- **Sinteză Vocală Stabilă (TTS):** Răspunsuri vorbite gestionate prin procese izolate (`multiprocessing` / `pyttsx3`) pentru a preveni blocajele pe Windows SAPI5.
- **Function Calling (Tools):**
  - **Automatizare Locală:** Deschidere de aplicații Windows (Browser, Notepad, Calculator etc.), căutare directă pe YouTube, scriere de fișiere text.
  - **Integrări Live API:** Verificare vreme în timp real și prognoză pe mai multe zile (**Open-Meteo API**), prețuri live crypto (**CoinGecko API**).
- **OCR & Viziune Ecran (În dezvoltare):** Scanarea ecranului cu `EasyOCR` și detectarea coordonatelor $(x, y)$ ale textului pentru automatizarea click-urilor de mouse cu `PyAutoGUI`.
- **Sistem de Securitate cu Confirmare Vocală:** Cere confirmare verbală (*yes/no*) înainte de a executa acțiuni pe sistem pentru comenzile primite prin microfon.

---

## Arhitectură & Tehnologii

- **Language:** Python 3.10+
- **LLM Engine:** Groq API (`qwen/qwen3.8-27b`)
- **Speech-to-Text:** `speech_recognition` + Groq Whisper (`whisper-large-v3-turbo`)
- **Text-to-Speech:** `pyttsx3` (cu izolare în `multiprocessing`)
- **Automation & Vision:** `pyautogui`, `easyocr`, `Pillow`
- **Networking:** `requests`
