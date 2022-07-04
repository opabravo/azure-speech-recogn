import time, json
import azure.cognitiveservices.speech as speechsdk
import os
import srt
import datetime


def load_api_key() -> str:
    try:
        with open('settings.json', 'r') as fp:
            api = json.load(fp)['api']
    except FileNotFoundError:
        api = save_api_key()
    return api


def save_api_key() -> str:
    while 1:
        api_key = input("請輸入Azure 語音服務 APIKEY: ")
        if api_key:
            break
    with open('settings.json', 'w') as fp:
        json.dump({'api': api_key}, fp)
    return api_key


FN = 'voice_test.wav'
API_KEY = load_api_key()
speech_config = speechsdk.SpeechConfig(subscription=API_KEY, region="eastus",
                                       speech_recognition_language='zh-TW')


def save_result(wav_name: str, result: str) -> str:
    if not os.path.isdir('output'):
        os.makedirs('output')

    index = 1
    while 1:
        file_path = f'output/{os.path.basename(wav_name)}_{index}.txt'
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding="utf-8") as f:
                f.write(result)
                print(f"------------\n已將結果儲存到: {file_path}")
            break
        index += 1


def result_handler(result):
    print("Recognizing...")

    if result.reason in [
        speechsdk.ResultReason.TranslatedSpeech,
        speechsdk.ResultReason.RecognizedSpeech,
    ]:
        print("Recognized: \n------------\n{}".format(result.text))
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print(f"No speech could be recognized: {result.no_match_details}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        print(f"Translation canceled: {result.cancellation_details.reason}")
        if result.cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {result.cancellation_details.error_details}")
            if 'Authentication error' in result.cancellation_details.error_details:
                print('\nAPI key錯誤，請重輸入...')
                save_api_key()
                result_handler(result)


def generate_srt(file_name):
    audio_input = speechsdk.audio.AudioConfig(filename=file_name)
    speech_config.request_word_level_timestamps()
    speech_config.enable_dictation()
    speech_config.output_format = speechsdk.OutputFormat(1)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    all_results = []
    transcript = []
    words = []

    # https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.recognitionresult?view=azure-python
    def handle_final_result(evt):
        all_results.append(evt.result.text)
        results = json.loads(evt.result.json)
        transcript.append(results['DisplayText'])
        confidence_list_temp = [item.get('Confidence') for item in results['NBest']]
        max_confidence_index = confidence_list_temp.index(max(confidence_list_temp))
        words.extend(results['NBest'][max_confidence_index]['Words'])

    done = False

    def stop_cb(evt):
        print(f'CLOSING on {evt}')
        nonlocal done
        done = True

    speech_recognizer.recognized.connect(handle_final_result)
    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
    speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    speech_recognizer.start_continuous_recognition()

    while not done:
        time.sleep(.5)

    speech_recognizer.stop_continuous_recognition()

    print("Printing all results:")
    print(all_results)

    speech_to_text_response = words

    def convertduration(t):
        x = t / 10000
        return int((x / 1000)), (x % 1000)

    ##-- Code to Create Subtitle --#

    # 3 Seconds
    bin = 3.0
    duration = 0
    transcriptions = []
    transcript = ""
    index, prev = 0, 0
    wordstartsec, wordstartmicrosec = 0, 0
    for i in range(len(speech_to_text_response)):
        # Forms the sentence until the bin size condition is met
        transcript = transcript + " " + speech_to_text_response[i]["Word"]
        # Checks whether the elapsed duration is less than the bin size
        if int((duration / 10000000)) < bin:
            wordstartsec, wordstartmicrosec = convertduration(speech_to_text_response[i]["Offset"])
            duration = duration + speech_to_text_response[i]["Offset"] - prev
            prev = speech_to_text_response[i]["Offset"]
            # transcript = transcript + " " + speech_to_text_response[i]["Word"]
        else:
            index = index + 1
            # transcript = transcript + " " + speech_to_text_response[i]["Word"]
            transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, wordstartsec, wordstartmicrosec),
                                               datetime.timedelta(0, wordstartsec + bin, 0), transcript))
            duration = 0
            # print(transcript)
            transcript = ""

    transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, wordstartsec, wordstartmicrosec),
                                       datetime.timedelta(0, wordstartsec + bin, 0), transcript))
    subtitles = srt.compose(transcriptions)
    with open("subtitle.srt", "w") as f:
        f.write(subtitles)


def translation_once_from_mic():
    """performs one-shot speech translation from input from an audio file"""
    # <TranslationOnceWithMic>
    # set up translation parameters: source language and target languages
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # Creates a translation recognizer using and audio file as input.
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config)

    # Starts translation, and returns after a single utterance is recognized. The end of a
    # single utterance is determined by listening for silence at the end or until a maximum of 15
    # seconds of audio is processed. It returns the recognized text as well as the translation.
    # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
    # shot recognition like command or query.
    # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
    print("請講一句話!")
    result_handler(recognizer.recognize_once())


def translation_once_from_file(file_name):
    """performs one-shot speech translation from input from an audio file"""
    # <TranslationOnceWithFile>
    # set up translation parameters: source language and target languages

    audio_config = speechsdk.audio.AudioConfig(filename=file_name)

    # Creates a translation recognizer using and audio file as input.
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config)

    # Starts translation, and returns after a single utterance is recognized. The end of a
    # single utterance is determined by listening for silence at the end or until a maximum of 15
    # seconds of audio is processed. The task returns the recognition text as result.
    # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
    # shot recognition like command or query.
    # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
    result = result_handler(recognizer.recognize_once())
    if not result:
        return print("There's no valid result! Not Saving")
    save_result(file_name, result)


def translation_continuous(file_name):
    """performs continuous speech translation from input from an audio file"""
    # <TranslationContinuous>
    # set up translation parameters: source language and target languages

    audio_config = speechsdk.audio.AudioConfig(filename=file_name)

    # Creates a translation recognizer using and audio file as input.
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config)

    def result_callback(event_type, evt):
        """callback to display a translation result"""
        print("{}: {}\n\tTranslations: {}\n\tResult Json: {}".format(
            event_type, evt, evt.result.translations.items(), evt.result.json))

    done = False

    def stop_cb(evt):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print(f'CLOSING on {evt}')
        nonlocal done
        done = True

    # Connect callbacks to the events fired by the speech recognizer
    recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
    recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
    recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    recognizer.session_stopped.connect(stop_cb)
    recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

    recognizer.stop_continuous_recognition()


def recognize_from_mic():
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    # 接收一句話，結束
    print("請講一句話!")
    result = speech_recognizer.recognize_once_async().get()
    print(f"翻譯: {result.text}")


if __name__ == '__main__':
    # translation_once_from_mic()
    # translation_once_from_file(FN)
    # translation_continuous(FN)
    # "C:\\Users\\GOD\\Downloads\\xxx (online-audio-converter.com).wav"
    generate_srt("C:\\Users\\GOD\\Downloads\\a6h1a-oy5i5.wav")
