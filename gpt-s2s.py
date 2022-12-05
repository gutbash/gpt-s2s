import keyboard
import os
import re
import time
import openai
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from playsound import playsound

# loads env variables file
load_dotenv()

### AUTH KEYS ###

AZURE_SPEECH_KEY = os.getenv("AZURE") #AZURE
OAI_API_KEY = os.getenv("YOUR_API_KEY") #OPENAI
openai.api_key=OAI_API_KEY #OPEN AI INIT

### AZURE ###

# configs tts
speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region="eastus")

## STT LANGUAGES ##

speech_config.speech_recognition_language="en-US"

#speech_config.speech_recognition_language="es-US"
#speech_config.speech_recognition_language="es-MX"
#speech_config.speech_recognition_language="es-PR"
#speech_config.speech_recognition_language="es-DO"
#speech_config.speech_recognition_language="es-SV"
#speech_config.speech_recognition_language="es-CU"

#speech_config.speech_recognition_language="yue-CN"
#speech_config.speech_recognition_language="zh-CN"

#speech_config.speech_recognition_language="vi-VN"

#speech_config.speech_recognition_language="ru-RU"

#speech_config.speech_recognition_language="ar-EG"
#speech_config.speech_recognition_language="ar-SY"
#speech_config.speech_recognition_language="ar-MA"

#speech_config.speech_recognition_language="fr-FR"

#speech_config.speech_recognition_language="km-KH"

#speech_config.speech_recognition_language="it-IT"

#speech_config.speech_recognition_language="fil-PH"

#speech_config.speech_recognition_language="ja-JP"

## TTS LANGUAGES ##
# other than Aria, style compatible (-empathetic) with Davis, Guy, Jane, Jason, Jenny, Nancy, Tony

# ENGLISH #
speech_config.speech_synthesis_voice_name='en-US-NancyNeural'
#speech_config.speech_synthesis_voice_name='en-US-JennyNeural'
#speech_config.speech_synthesis_voice_name='en-US-AriaNeural'
#speech_config.speech_synthesis_voice_name='en-US-JennyMultilingualNeural'

# SPANISH #
#speech_config.speech_synthesis_voice_name='es-US-PalomaNeural' # united states
#speech_config.speech_synthesis_voice_name='es-MX-CarlotaNeural' # mexican
#speech_config.speech_synthesis_voice_name='es-PR-KarinaNeural' # puerto rican
#speech_config.speech_synthesis_voice_name='es-DO-RamonaNeural' # dominican
#speech_config.speech_synthesis_voice_name='es-SV-LorenaNeural' # salvadorean
#speech_config.speech_synthesis_voice_name='es-CU-BelkysNeural' # cuban

# CHINESE #
#speech_config.speech_synthesis_voice_name='yue-CN-XiaoMinNeural' # cantonese
#speech_config.speech_synthesis_voice_name='zh-CN-XiaochenNeural' # mandarin

# VIETNAMESE #
#speech_config.speech_synthesis_voice_name='vi-VN-HoaiMyNeural'

# RUSSIAN #
#speech_config.speech_synthesis_voice_name='ru-RU-DariyaNeural'

# ARABIC #
#speech_config.speech_synthesis_voice_name='ar-EG-SalmaNeural' # egyptian
#speech_config.speech_synthesis_voice_name='ar-SY-AmanyNeural' # syrian
#speech_config.speech_synthesis_voice_name='ar-MA-MounaNeural' # moroccan

# FRENCH #
#speech_config.speech_synthesis_voice_name='fr-FR-BrigitteNeural'

# KHMER #
#speech_config.speech_synthesis_voice_name='km-KH-SreymomNeural'

# ITALIAN #
#speech_config.speech_synthesis_voice_name='it-IT-ElsaNeural'

# TAGALOG #
#speech_config.speech_synthesis_voice_name='fil-PH-BlessicaNeural'

# JAPANESE #
#speech_config.speech_synthesis_voice_name='ja-JP-MayuNeural'

# sets voice
voice = speech_config.speech_synthesis_voice_name

# sets tts sample rate
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Raw48Khz16BitMonoPcm)

# microphone device stt 
stt_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
# speaker device tts
tts_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# inits stt
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=stt_config)
# inits tts
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=tts_config)

# sets up identifiers for conversation
bot = "Nancy"
user = "Bash"

### SETUP VARIABLES ###
# concats message history for re-insertion with every prompt
context = ""
messages = []
# last response from GPT
raspuns = ""
raspunsF = ""
# holds emotional response chosen by GPT-3
style = ""
# counts number of times user silence for input
silenceCount = 0
# counts number of messages in conversation history 
messageCount = 0

""" TONE_GPT3()
1. inputs and reads user prompt
3. chooses emotional response from given list of styles
2. returns style/emotion
"""
def tone_gpt3(zice):
    toneLabel = openai.Completion.create(
        engine="text-davinci-003",
        #prompt="Read the following interaction, then pick just one of the emotions for "+bot+" to respond to "+user+" with from this list only: [unfriendly, angry, angry, shouting, shouting, sad, terrified, whispering, whispering, whispering, hopeful, cheerful, excited, friendly].\n"+bot+": "+raspuns+"\n"+user+": "+zice+"\n\nEmotion: [",
        prompt="Read the following interaction, then pick just one of the emotions for "+bot+" to respond to "+user+" with from this list only: [friendly, empathetic, cheerful, excited, hopeful, unfriendly, angry, shouting, sad, terrified, whispering].\n"+bot+": "+raspuns+"\n"+user+": "+zice+"\n\nEmotion: [",
        temperature=0.0,
        max_tokens=12,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=[user+":", bot+":", "Emotion: [", ","],
    )
    return toneLabel

def concatContext():
    
    global messages
    global context
    
    if len(messages) == 6:
        messages.pop()
        
    print(len(messages))
        
    for message in messages:
        context += message

""" CHAT_GPT3()
1. inputs and reads user prompt
2. responds with given style from TONE_GPT3()
3. returns response
"""
def chat_gpt3(zice):
    response = openai.Completion.create(
        engine="text-davinci-003",
        #prompt= bot+" is helping "+user+" speak Spanish. "+context+"\n"+user+": "+zice+"\n"+bot+":",
        prompt= "This is a chat between "+bot+" and "+user+". You are "+bot+". "+bot+" loves to have interesting and random conversations. "+bot+" is also very funny and witty. "+bot+" speaks informally and casually, constantly using filler words such as 'um', 'uh', 'like', 'very', 'really', 'just', 'you know', 'i mean', 'i guess', 'totally', 'literally', 'seriously', and others when speaking."+context+"\n"+user+": "+zice+"\n"+bot+" ["+style+"]:",
        temperature=1.0,
        max_tokens=256,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=2.0,
        stop=[user+":", bot+":", "["],
        echo=False,
    )
    return response

""" TTS()
1. inputs response SSML from CHAT_GPT()
2. streams async synthesis
"""
def tts(ssml):
    global speech_synthesis_result
    #speech_recognizer.stop_speaking_async()
    speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml).get()
    #speech_synthesis_result = speech_synthesizer.start_speaking_ssml_async(ssml)
"""
def stt(model="base", english=False, verbose=False, energy=300, pause=0.5, dynamic=True):
    
    temp_dir = tempfile.mkdtemp()
    save_path = os.path.join(temp_dir, "temp.wav")

    audio_model = whisper.load_model(model)
    
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic

    with sr.Microphone(sample_rate=16000) as source:
            
        # prints status
        print("|||||||||| LISTENING ||||||||||")
        
        audio = r.listen(source)
        data = io.BytesIO(audio.get_wav_data())
        audio_clip = AudioSegment.from_file(data)
        audio_clip.export(save_path, format="wav")

        if english:
            result = audio_model.transcribe(save_path,language='english')
        else:
            result = audio_model.transcribe(save_path)

        if not verbose:
            predicted_text = result["text"]
            print("You said: " + predicted_text)
        else:
            print(result)
    
    return predicted_text
"""
while (True):

    try:
        
        # controls whether interaction has been recieved and processed or not
        done = False
        
        # given input stt
        # generates style and response from GPT-3
        # synthesizes response tts
        def textSpeech(inp):
            
            inp.encode("utf-8")
            
            # parses and formats user input
            prompt = user+": "+inp

            # global counter and helper variables
            global silenceCount
            global context
            global style
            global raspuns
            global raspunsF

            # processes non-silent interaction
            if inp != "":
                
                # prints status
                #print("NON-SILENCE")
                print(prompt)

                # gets style GPT would like to respond with
                style = ((tone_gpt3(inp)).choices[0].text).split("]")[0]
                #print(style)

                # gets GPT text message response completion
                raspuns = (chat_gpt3(inp)).choices[0].text
                
                # formats raspuns
                raspunsF = bot+" ["+style+"]: " + raspuns
                #raspunsF = bot+": "+raspuns

                # prints raspuns
                print(raspunsF)
                #print(raspuns)
                
                messages.append("\n"+prompt+"\n"+raspunsF)

                # concats message to memory/history
                concatContext()

                # SSML for TTS with response and style
                xmlStringReg = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="'''+voice+'''">
                '''+ raspuns +'''
                </voice>
                </speak>'''
                xmlString = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
                xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
                <voice name="'''+voice+'''">
                <prosody rate="medium">
                <mstts:express-as style="'''+style+'''" styledegree="2">
                '''+ raspuns +'''
                </mstts:express-as>
                </prosody>
                </voice>
                </speak>'''

                # synthesizes TTS with input SSML
                tts(xmlString)

                # resets silence count to 0
                silenceCount = 0

                # marks interaction
                done = True

            # processes silent interaction
            else:

                # checks if user has been silent for certain amount of time
                if silenceCount == 2:
                    
                    # imitates silent input
                    prompt = user+": ..."

                    # prints status
                    #print("SILENCE PROMPT")
                    print(prompt)

                    # gets style GPT would like to respond with
                    style = ((tone_gpt3("...")).choices[0].text).split("]")[0]
                    #print(style)

                    # gets GPT text message response completion
                    raspuns = (chat_gpt3("...")).choices[0].text

                    # formats raspuns
                    raspunsF = bot+" ["+style+"]: " + raspuns
                    #raspunsF = bot+": "+raspuns

                    # prints raspuns
                    print(raspunsF)

                    messages.append("\n"+prompt+"\n"+raspunsF)

                    # concats message to memory/history
                    concatContext()

                    # SSML for TTS with response and style
                    xmlStringReg = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                    <voice name="'''+voice+'''">
                    '''+ raspuns +'''
                    </voice>
                    </speak>'''
                    xmlString = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
                    xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
                    <voice name="'''+voice+'''">
                    <prosody rate="medium">
                    <mstts:express-as style="'''+style+'''" styledegree="2">
                    '''+ raspuns +'''
                    </mstts:express-as>
                    </prosody>
                    </voice>
                    </speak>'''

                    # synthesizes TTS with input SSML
                    tts(xmlString)

                    # resets silence count to 0
                    silenceCount = 0

                    # marks interaction
                    done = True

                # increases silence count
                #print("SILENCE")
                silenceCount += 1
        
        # listens for speech
        while not done:
            
            playsound('start.mp3', False)
            print("|||||||||| LISTENING ||||||||||")
            #playsound('start.mp3', False)

            # prompts for text input
            #input = input()

            # processes text input
            #textSpeech(input)
            
            # gets azure stt
            speech_recognition_result = speech_recognizer.recognize_once_async().get()

            #playsound('stop.mp3', False)

            # gets tts from azure stt
            speech_recognizer.recognized.connect(textSpeech(speech_recognition_result.text))

            # gets whisper stt
            #speech_recognition_result = stt()

            # gets tts from whisper stt
            #textSpeech(speech_recognition_result)

    # excepts if not understood
    except Exception as e:
        print("Could not understand", e)