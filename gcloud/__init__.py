import os

from google.cloud import translate
from google.cloud import speech_v1p1beta1 as speech

import config

project = config.GOOGLE_CLOUD_PROJECT_NUMBER_OR_ID
languages_accepted = list(config.SORTED_PLAYLIST_IDS.keys())

if len(languages_accepted) > 4:
    raise ValueError("You can only have a maximum of 4 languages in SORTED_PLAYLIST_IDS")


def set_service_account_path(path):
    if not path:
        return

    if not os.path.exists(path):
        raise FileNotFoundError(f"Service account file does not exist: {path}")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path


def detect_language_from_text(text):
    client = translate.TranslationServiceClient()

    location = "global"

    parent = f"projects/{project}/locations/{location}"

    response = client.detect_language(
        content=text,
        parent=parent,
        mime_type="text/plain",
    )

    langs = []

    for language in response.languages:
        code = language.language_code
        confidence = language.confidence

        code = code.lower().split("-")[0]

        if code in languages_accepted:
            langs.append({"code": code, "confidence": confidence})

    langs.sort(key=lambda d: d["confidence"], reverse=True)

    return langs


def detect_language_from_audio(file: str | bytes):
    if isinstance(file, str):
        with open(file, "rb") as f:
            file = f.read()

    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=file)  # type: ignore

    first_lang = languages_accepted[0]
    second_lang = languages_accepted[1:]

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,  # type: ignore
        sample_rate_hertz=44100,  # type: ignore
        audio_channel_count=2,  # type: ignore
        language_code=first_lang,
        alternative_language_codes=second_lang,  # type: ignore
    )

    response = client.recognize(config=config, audio=audio)

    langs_raw = []
    langs = []
    langs_done = []

    for result in response.results:
        code = result.language_code
        code = code.lower().split("-")[0]

        langs_raw.append(code)

    for code in langs_raw:
        if code not in languages_accepted:
            continue

        if code in langs_done:
            continue

        confidence = langs_raw.count(code) / len(langs_raw)

        langs.append({"code": code, "confidence": confidence})

        langs_done.append(code)

    langs.sort(key=lambda d: d["confidence"], reverse=True)

    return langs
