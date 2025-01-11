from flask import Flask, render_template, request, redirect, url_for
import os
import random
from gtts import gTTS
from difflib import SequenceMatcher
import speech_recognition as sr
import time

app = Flask(__name__)

# Sprachdatenbank
sentences = {
    "de": {
        "leicht": [
            "Hallo, wie geht es dir?",
            "Ich liebe Programmieren mit Python.",
            "Der Himmel ist heute sehr blau."
        ],
        "mittel": [
            "Künstliche Intelligenz ist faszinierend.",
            "Ich trinke gerne Kaffee am Morgen.",
            "Die Blumen im Garten blühen prächtig."
        ],
        "schwer": [
            "Die tiefgreifende Analyse der Daten ist essenziell.",
            "Kollaboratives Arbeiten erfordert Kommunikation und Geduld.",
            "Die Wolken spiegeln sich im ruhigen Wasser des Sees wider."
        ]
    },
    "fr": {
        "leicht": [
            "Bonjour, comment ça va?",
            "J'adore programmer en Python.",
            "Le ciel est très bleu aujourd'hui."
        ],
        "mittel": [
            "L'intelligence artificielle est fascinante.",
            "Je bois du café le matin.",
            "Les fleurs dans le jardin sont magnifiques."
        ],
        "schwer": [
            "L'analyse approfondie des données est essentielle.",
            "La collaboration nécessite communication et patience.",
            "Les nuages se reflètent dans l'eau calme du lac."
        ]
    },
    "en": {
        "leicht": [
            "Hello, how are you?",
            "I love programming with Python.",
            "The sky is very blue today."
        ],
        "mittel": [
            "Artificial intelligence is fascinating.",
            "I enjoy drinking coffee in the morning.",
            "The flowers in the garden are blooming beautifully."
        ],
        "schwer": [
            "In-depth data analysis is essential.",
            "Collaborative work requires communication and patience.",
            "The clouds are reflected in the calm water of the lake."
        ]
    }
}

# Globale Variablen
current_language = "de"
current_level = "leicht"
current_index = 0
current_sentence = sentences[current_language][current_level][current_index]


def generate_audio(sentence, lang):
    """Erstellt eine Audio-Datei."""
    tts = gTTS(text=sentence, lang=lang)
    filename = "static/output.mp3"
    if os.path.exists(filename):
        os.remove(filename)
    tts.save(filename)


def similarity_score(sentence1, sentence2):
    """Berechnet die Ähnlichkeit zweier Sätze."""
    return SequenceMatcher(None, sentence1.lower(), sentence2.lower()).ratio()


@app.route("/", methods=["GET", "POST"])
def index():
    global current_language, current_level, current_index, current_sentence

    # Sprache ändern
    if request.method == "POST":
        if "language" in request.form:
            current_language = request.form["language"]
            current_index = 0

        # Schwierigkeit ändern
        if "level" in request.form:
            current_level = request.form["level"]
            current_index = 0

        # Weiter zum nächsten Satz
        if "next" in request.form:
            current_index = (current_index + 1) % len(sentences[current_language][current_level])

        # Erneut anhören
        if "repeat" in request.form:
            pass  # Satz bleibt gleich

        # Satz zum Abspielen
        current_sentence = sentences[current_language][current_level][current_index]
        generate_audio(current_sentence, current_language)

    return render_template("index.html",
                           sentence=current_sentence,
                           language=current_language,
                           level=current_level,
                           timestamp=int(time.time()))


@app.route("/check", methods=["POST"])
def check_speech():
    """Sprachanalyse durchführen."""
    global current_sentence, current_language

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source)
            user_response = recognizer.recognize_google(audio, language=current_language)
            score = round(similarity_score(current_sentence, user_response) * 100)
            return render_template("result.html", sentence=current_sentence, user_response=user_response, score=score)
        except sr.UnknownValueError:
            return render_template("result.html", error="Ich konnte dich nicht verstehen.")
        except sr.RequestError:
            return render_template("result.html", error="Fehler bei der Anfrage.")


if __name__ == "__main__":
    app.run(debug=True)
