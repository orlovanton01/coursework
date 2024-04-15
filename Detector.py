import PySimpleGUI as sg
import speech_recognition  # распознавание пользовательской речи (Speech-To-Text)
import pyttsx3  # синтез речи (Text-To-Speech)
import json  # работа с json-файлами и json-строками
import requests
import pickle
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model
import threading

with open('Keys.txt') as f:
    s=f.read().split('\n')

catalog_id=s[0]
API_key=s[1]

class SimpleWorker:
    def __init__(self, window: sg.Window, text):
        # INIT Worker's variable
        self.run = False
        self.window = window
        self.text = text

    def start_thread(self):
        # Only Do something if not running
        if not self.run:
            # Create Thread from job_processing function
            self.job_threading = threading.Thread(target=self.job_processing)
            self.job_threading.start()

    def stop_thread(self):
        # Tell Worker to stop
        self.run = False
        return self.text

    def job_processing(self):
        # Set to run
        self.run = True
        prev_command = ""
        flag = True
        try:
            while self.run:
                if not self.run:
                    break
                voice_input = record_and_recognize_audio(duration, self.text, self.run, mode)
                if voice_input == "":
                    if self.run:
                        get_result(self.text, True, mode)
                    else:
                        get_result(self.text, False, mode)
                    break
                    reset()
                elif voice_input == None:
                    break
                    reset()
                if not self.run:
                    break
                sg.cprint(voice_input)
                self.text += voice_input
                if mode == "assistant":
                    # отделение комманд от дополнительной информации (аргументов)
                    voice_input = voice_input.split(" ")
                    command = voice_input[0]
                    answer = get_answer(command, prev_command, flag)
                    play_voice_assistant_speech(answer)
                    prev_command = answer
                    sg.cprint(answer)
                    self.text += answer
                else:
                    if self.run:
                        get_result(self.text, True, mode)
                    else:
                        get_result(self.text, False, mode)
                    break
                    reset()
                if not self.run:
                    break
        except:
            pass

def show_popup(text, title):
    sg.popup(text, title=title, button_justification='c')

def enable_field(k):
    window[k].update(disabled=False)

def disable_field(k):
    window[k].update(disabled=True)

def clear_field(k):
    window[k].update('')

def reset():
    disable_field('stop')
    for k in 'combo', 'input', 'reset':
        enable_field(k)

max_phrases_len = 141

with open('tokenizer.pickle', 'rb') as handle:
    tokenizer = pickle.load(handle)

model_cnn = load_model('best_model_cnn.h5')

class VoiceAssistant:
    """
    Настройки голосового ассистента, включающие имя, пол, язык речи
    """
    name = ""
    sex = ""
    speech_language = ""
    recognition_language = ""


def setup_assistant_voice():
    """
    Установка голоса по умолчанию (индекс может меняться в
    зависимости от настроек операционной системы)
    """
    voices = ttsEngine.getProperty("voices")

    assistant.recognition_language = "ru-RU"
    # Microsoft Irina Desktop - Russian
    ttsEngine.setProperty("voice", voices[0].id)


def play_voice_assistant_speech(text_to_speech):
    """
    Проигрывание речи ответов голосового ассистента (без сохранения аудио)
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    ttsEngine.say(str(text_to_speech))
    ttsEngine.runAndWait()

def get_result(text, flag, mode):
    if text == "":
        if flag:
            sg.cprint("Можете ли вы проверить свой микрофон, пожайлуйста?")
    else:
        if flag:
            if mode == 'assistant':
                sg.cprint('Нет ответа')
        sequences = tokenizer.texts_to_sequences([text])
        x = pad_sequences(sequences, maxlen=max_phrases_len)
        result = model_cnn.predict(x, verbose=0)
        if result[0][0]<=0.29:
            sg.cprint('Вы разговариваете с представителем банка', colors='black on yellow')
        else:
            sg.cprint('Вы разговариваете с мошенником', colors='black on yellow')
    reset()

def record_and_recognize_audio(duration, text, run, mode):
    """
    Запись и распознавание аудио
    """
    with microphone:
        recognized_data = ""

        try:
            sg.cprint("Прослушивание...")
            audio = recognizer.listen(microphone, duration, duration)

        except speech_recognition.WaitTimeoutError:
            if run:
                get_result(text, True, mode)
            else:
                get_result(text, False, mode)
            return

        # использование online-распознавания через Google
        try:
            sg.cprint("Начало распознавания...")
            recognized_data = recognizer.recognize_google(audio, language="ru")

        except speech_recognition.UnknownValueError:
            pass

        # в случае проблем с доступом в Интернет происходит выброс ошибки
        except speech_recognition.RequestError:
            sg.cprint("Проверьте своё подключение к интернету, пожайлуйста")
            reset()

        return recognized_data

def get_answer(command, prev_command, flag):
    if flag:
        prompt = {
            "modelUri": f"gpt://{catalog_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты-разговариваешь с человеком по телефону. Можешь отвечать только одной фразой"
                },
                {
                    "role": "user",
                    "text": command
                }
            ]
        }
        flag = False
    else:
        prompt = {
            "modelUri": f"gpt://{catalog_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты-разговариваешь с человеком по телефону. Можешь отвечать только одной фразой"
                },
                {
                    "role": "assistant",
                    "text": prev_command
                },
                {
                    "role": "user",
                    "text": command
                }
            ]
        }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_key}"
    }

    response = requests.post(url, headers=headers, json=prompt)
    result = json.loads(response.text).get('result').get('alternatives')[0].get('message').get('text')
    return result

# инициализация инструментов распознавания и ввода речи
recognizer = speech_recognition.Recognizer()
microphone = speech_recognition.Microphone()

# инициализация инструмента синтеза речи
ttsEngine = pyttsx3.init()

# настройка данных голосового помощника
assistant = VoiceAssistant()
assistant.name = "Alice"
assistant.sex = "female"
assistant.speech_language = "ru"

# установка голоса по умолчанию
setup_assistant_voice()

first_column = [
    [sg.Text('Выбор режима', s=23, justification='c')],
    [sg.Combo(['Самостоятельный разговор', 'С ассистентом'], enable_events=True, k='combo', readonly=True)]
]

second_column = [
    [sg.Text('Время записи в секундах')],
    [sg.InputText(s=22, justification='c', enable_events=True, disabled=True, k='input')]
]

# All the stuff inside your window.
layout = [
    [sg.Column(first_column), sg.Column(second_column)],
    [
     sg.Button('Начать запись', s=14, button_color=('white', 'springgreen4'), k='start', enable_events=True, disabled=True),
     sg.Button('Остановить запись', s=14, button_color=('white', 'firebrick3'), k='stop', enable_events=True, disabled=True),
     sg.Button('Сбросить', s=14, button_color=('white', 'black'), k='reset', enable_events=True, disabled=True)
    ],
    [sg.Text('Окно вывода', s=47, justification='c')],
    [sg.Multiline(s=(52, 10), k='multiline', reroute_cprint=True, disabled=True, autoscroll=True)],
]

# Create the Window
window = sg.Window('Детектор', layout)

show_popup('Добро пожаловать. Для начала выберите режим работы', 'Приветствие')

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == 'combo':
        enable_field('input')
        if values['combo'] == 'Самостоятельный разговор':
            show_popup('Введите время записи всего диалога', 'Сообщение')
            mode = 'self'
        else:
            show_popup('Введите время записи одной фразы', 'Сообщение')
            mode = 'assistant'
        enable_field('reset')
    if event == 'input':
        try:
            int_value = int(values['input'])
        except:
            show_popup('Введите в поле число', 'Предупреждение')
            clear_field('input')
        duration = int_value
        enable_field('start')
    if event == 'reset':
        for k in 'combo', 'input', 'multiline':
            clear_field(k)
        for k in 'reset', 'start', 'stop':
            disable_field(k)
    if event == 'start':
        clear_field('multiline')
        for k in 'combo', 'input', 'reset':
            disable_field(k)
        enable_field('stop')
        text = ""
        worker = SimpleWorker(window=window, text=text)
        worker.start_thread()
    if event == 'stop':
        text = worker.stop_thread()
        show_popup('Остановлено', 'Предупреждение')
        if text != '':
            get_result(text, False, mode)
        reset()
    if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
        break

window.close()