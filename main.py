import json
import re
import soundfile as sf
from PIL import Image
from customtkinter import *
from deepgram import *
from googletrans import Translator
from gtts import gTTS
from moviepy.editor import *
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
from pydub.effects import *

DEEPGRAM_KEY = "b7ac08a38e4931285172d4fbf4ee8e3a0e718ead"

window = CTk()
window.geometry("680x498")
window.title("small example app")
window.minsize(680, 498)

# create 2x2 grid system
window.grid_rowconfigure(0, weight=1)
window.grid_columnconfigure((0, 1), weight=1)
mass = ["English", "Italian", "Japanese", "Russian", "Spanish", "German"]


def submit():
    global lang_in, lang
    initial_language = w.get()
    final_language = z.get()

    print(sf.available_formats())
    print(sf.__libsndfile_version__)
    #videoclip = VideoFileClip(labelPath.cget("text"))
    # Insert Local Audio File Path
    # videoclip.audio.write_audiofile("test.wav", codec='pcm_s16le')
    # initialize the recognizer
    # r = sr.Recognizer()

    if initial_language == "English":
        lang_in = 'en'
    elif initial_language == "Italian":
        lang_in = 'it'
    elif initial_language == "Spanish":
        lang_in = 'es'
    elif initial_language == "Russian":
        lang_in = 'ru'
    elif initial_language == "German":
        lang_in = 'de'
    elif initial_language == "Japanese":
        lang_in = 'ja'
    # open the file

    deepgram = Deepgram(DEEPGRAM_KEY)
    print("begin transcript")
    with open(labelPath.cget("text"), "rb") as video:
        source = {'buffer' : video, 'mimetype' : 'video/mp4'}
        options = {"punctuate": True, "language": "en-US"}

        response = deepgram.transcription.sync_prerecorded(source, options)
        print(json.dumps(response, indent=4))

    subtitles = []
    for word in response["results"]["channels"][0]["alternatives"][0]["words"]:
        word, start, end = word["word"], word["start"], word["end"]
        subtitles.append([word, start, end])

    print(response["results"]["channels"][0]["alternatives"][0]["transcript"])
    textInitiate = re.split(r'(?<=\w[.!?]) ', response["results"]["channels"][0]["alternatives"][0]["transcript"])
    print(textInitiate)
    translator = Translator()
    textDest=[]
    i=1
    os.makedirs("temp", exist_ok=True)
    audio_folder = os.path.join(os.getcwd(), "temp")
    translations=[]
    durations=[]
    silence=[]
    for sentence in (textInitiate):
        translation = translator.translate(sentence, dest="ru")
        print(translation.text, end=" ")
        space=sentence.count(" ")
        durations.append(subtitles[i-1+space][2]-subtitles[i-1][1])
        print(subtitles[i-1+space][2]-subtitles[i-1][1])
        if i!=1:
            silence.append(subtitles[i-1][1]-subtitles[i-2][2])
        i+=space+1
        translations.append(translation.text)

    print("gtts")
    audio_array=[]
    for line in translations:
        tts = gTTS(line, lang="ru")
        audio_array.append(tts)

    for i, audio in enumerate(audio_array):
        audio.save(os.path.join(audio_folder, f"{i}.wav"))
        print(i)
    final_audio=AudioSegment.empty()
    final_audio+=AudioSegment.silent(subtitles[0][1])
    print("len - "+str(len(final_audio)))
    for i in range(len(audio_array)):

        audioclip = AudioFileClip(os.path.join(audio_folder, f"{i}.wav"))
        dur = audioclip.duration
        print(dur)
        print(durations[i])
        print(dur / durations[i])
        audioclip.close()
        print(str(i) + " - very slow")

        tempAudio = AudioSegment.from_file(os.path.join(audio_folder, f"{i}.wav"))
        if dur > durations[i]:
            coef = dur / durations[i]
            tempAudio = speedup(tempAudio, coef)
        final_audio+=tempAudio
        print("len sound - " + str(len(final_audio)))
        if i!=len(audio_array)-1:
            final_audio+=AudioSegment.silent(duration=silence[i]*1000)
            print("len silence - " + str(len(final_audio)))
        #tts.save(f"{count}.mp3")
    final_audio.export("temp/test.wav")

    videoclip = VideoFileClip(labelPath.cget("text"))
    audioclip = AudioFileClip("temp/test.wav")

    new_audioclip = CompositeAudioClip([audioclip])
    videoclip = videoclip.without_audio()
    videoclip.audio = new_audioclip

    videoclip.write_videofile("final_clip.mp4")
    #os.rmdir("temp")
    # if final_language == "English":
    #     lang = 'en'
    # elif final_language == "Italian":
    #     lang = 'it'
    # elif final_language == "Spanish":
    #     lang = 'es'
    # elif final_language == "Russian":
    #     lang = 'ru'
    # elif final_language == "German":
    #     lang = 'de'
    # elif final_language == "Japanese":
    #     lang = 'ja'


def clear():
    print("clear")
    pass


def get_path(event):
    print(event.data)


def _resize_image(event):
    new_width = event.width - 140
    new_height = event.height - 60
    my_image = CTkImage(light_image=Image.open("temp/frame.jpg"), size=(new_width, new_height))

    frameInputVideo.configure(image=my_image)


def selectFile(event):
    filetypes = (
        ("Video files", "*.mp4;*.flv;*.avi;*.mkv"),
        ('All files', '*.*')
    )

    filename = filedialog.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes
    )
    labelPath.configure(text=filename)
    video_clip = VideoFileClip(filename)

    os.makedirs("temp", exist_ok=True)
    video_clip.save_frame("temp/frame.jpg", 10)
    my_image = CTkImage(light_image=Image.open("temp/frame.jpg"), size=(680, 320))
    frameInputVideo.configure(image=my_image)
    frameInputVideo.bind('<Configure>', _resize_image)
    video_clip.close()

#
frameInputVideo = CTkLabel(master=window, text="", bg_color="grey18")
frameInputVideo.grid(row=0, column=0, columnspan=2, sticky="nsew")

frameInputVideo.bind('<Button-1>', selectFile)

labelPath = CTkLabel(master=window, text="Путь до видео")
labelPath.grid(row=1, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="nsew")

labelInput = CTkLabel(master=window, text="Выберите исходный язык")
labelInput.grid(row=2, column=0, padx=20, pady=(20, 10), sticky="nsew")
w = CTkOptionMenu(master=window, values=mass)
w.grid(row=2, column=1, padx=20, pady=(20, 10), sticky="ew")

labelOutput = CTkLabel(master=window, text="Выберите язык, на который\n будет переведено видео")
labelOutput.grid(row=3, column=0, padx=20, pady=(20, 10), sticky="nsew")
z = CTkOptionMenu(master=window, values=mass)
z.grid(row=3, column=1, padx=20, pady=(20, 10), sticky="ew")
z.set("Russian")

frameButton = CTkFrame(master=window, height=20, corner_radius=8)
frameButton.grid(row=4, column=0, columnspan=2, sticky="nsew")

buttonSubmit = CTkButton(window, text="Исполнить", command=submit, font=("Arial", 14), corner_radius=8)
buttonSubmit.grid(row=4, column=1, padx=40, pady=15, sticky="nsew")

buttonClear = CTkButton(window, text="Очистить", command=clear, font=("Arial", 14))
buttonClear.grid(row=4, column=0, padx=40, pady=15, sticky="nsew")

window.mainloop()
