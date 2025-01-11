from flask import Flask, render_template, request
import re
import os
from gtts import gTTS
from difflib import SequenceMatcher
import speech_recognition as sr
import time

app = Flask(__name__)

# Paths to sentence files (organized by language and level)
sentence_files = {
    "de": {
        "leicht": "sentences/de_leicht.txt",
        "mittel": "sentences/de_mittel.txt",
        "schwer": "sentences/de_schwer.txt"
    },
    "fr": {
        "leicht": "sentences/fr_leicht.txt",
        "mittel": "sentences/fr_mittel.txt",
        "schwer": "sentences/fr_schwer.txt"
    },
    "en": {
        "leicht": "sentences/en_leicht.txt",
        "mittel": "sentences/en_mittel.txt",
        "schwer": "sentences/en_schwer.txt"
    }
}

# Global variables
current_language = "de"
current_level = "leicht"
current_index = 0
current_sentences = []
current_sentence = ""


def load_sentences(language, level):
    """Loads sentences from a text file for the given language and level."""
    filepath = sentence_files[language].get(level)
    if filepath and os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    else:
        return []


def generate_audio(sentence, lang):
    """Creates an audio file."""
    tts = gTTS(text=sentence, lang=lang)
    filename = "static/output.mp3"
    if os.path.exists(filename):
        os.remove(filename)
    tts.save(filename)


def clean_string(input_string):
    """Remove all non-alphanumeric characters."""
    return re.sub(r'[^a-zA-Z0-9 ]', '', input_string)


def similarity_score(sentence1, sentence2):
    """Calculate similarity while ignoring symbols."""
    cleaned_sentence1 = clean_string(sentence1)
    cleaned_sentence2 = clean_string(sentence2)

    # Use SequenceMatcher to compare cleaned sentences
    return SequenceMatcher(None, cleaned_sentence1.lower(), cleaned_sentence2.lower()).ratio()


@app.route("/", methods=["GET", "POST"])
def index():
    global current_language, current_level, current_index, current_sentences, current_sentence

    # Handle POST requests for changing settings or navigating sentences
    if request.method == "POST":
        if "language" in request.form:
            current_language = request.form["language"]
            current_index = 0
            current_sentences = load_sentences(current_language, current_level)

        if "level" in request.form:
            current_level = request.form["level"]
            current_index = 0
            current_sentences = load_sentences(current_language, current_level)

        if "next" in request.form:
            # Ensure we don't go out of bounds
            if current_sentences:
                current_index = (current_index + 1) % len(current_sentences)
            else:
                current_index = 0  # Fallback if no sentences loaded

        if "repeat" in request.form:
            pass  # Sentence remains unchanged

    # If sentences are empty, try to load them
    if not current_sentences:
        current_sentences = load_sentences(current_language, current_level)

    if current_sentences:
        current_sentence = current_sentences[current_index]
    else:
        current_sentence = "No sentences available."  # Fallback if no sentences are loaded

    generate_audio(current_sentence, current_language)

    return render_template("index.html",
                           sentence=current_sentence,
                           language=current_language,
                           level=current_level,
                           timestamp=int(time.time()))


@app.route("/check", methods=["POST"])
def check_speech():
    """Performs speech analysis."""
    global current_sentence, current_language

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source)
            user_response = recognizer.recognize_google(audio, language=current_language)
            score = round(similarity_score(current_sentence, user_response) * 100)
            return render_template("result.html", sentence=current_sentence, user_response=user_response, score=score)
        except sr.UnknownValueError:
            return render_template("result.html", error="I could not understand you.")
        except sr.RequestError:
            return render_template("result.html", error="Error during the request.")
        except Exception as e:
            return render_template("result.html", error=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    app.run(debug=True)
