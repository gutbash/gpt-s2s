#from curses import echo
from tkinter.ttk import Style
from unittest import result
from urllib import response
from urllib.parse import uses_query
from matplotlib.pyplot import text
import nltk
from nltk.stem import LancasterStemmer
import numpy as np
import pickle
import random
import json
from gtts import gTTS
import os
import time
import boto3
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
import openai
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import xml.etree.ElementTree as ET
import xmltodict

# loads env variables file
load_dotenv()

### AUTH KEYS ###
AZURE_SPEECH_KEY = os.getenv("AZURE") #AZURE
OAI_API_KEY = os.getenv("YOUR_API_KEY") #OPENAI
openai.api_key=OAI_API_KEY #OPEN AI INIT
AWS_ID_KEY = os.getenv("AWS_ID_KEY") #AWS ID
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY") #AWS KEY
WIT_AI_KEY = os.getenv("WIT_AI_KEY") #WIT

### AZURE ###
# configs tts voice
speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region="eastus")
#speech_config.speech_recognition_language="en-US"
speech_config.speech_recognition_language="es-US"
#speech_config.speech_recognition_language="fr-CA"
#speech_config.speech_synthesis_voice_name='en-US-AriaNeural'
speech_config.speech_synthesis_voice_name='es-MX-CarlotaNeural'
#speech_config.speech_synthesis_voice_name = 'zh-CN-XiaomoNeural'
voice = speech_config.speech_synthesis_voice_name

# microphone device stt 
stt_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
# speaker device tts
tts_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# inits stt
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=stt_config)
# inits tts
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=tts_config)
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff44100Hz16BitMonoPcm)

# sets up identifiers for conversation
user = "Sebastian"
bot = "Carlota"

### IMPORTANT SETUP VARIABLES ###
# concats message history for re-insertion with every prompt
context = ""
# last response from GPT
raspuns = ""
raspunsF = ""
# holds emotional response chosen by GPT-3
style = ""
# counts number of messages in conversation history 
messageCount = 0
# counts number of times user silence for input
silenceCount = 0

""" TONE_GPT3()
1. inputs and reads user prompt
3. chooses emotional response from given list of styles
2. returns style/emotion
"""
def tone_gpt3(zice):
    toneLabel = openai.Completion.create(
        engine="text-davinci-002",
        prompt="Read the following interaction, then pick just one of the most appropriate emotions for "+bot+" to respond to "+user+" with from this list only: [friendly, empathetic, hopeful, cheerful, excited, unfriendly, angry, shouting, sad, terrified, whispering].\n"+bot+": "+raspuns+"\n"+user+": "+zice+"\n\nEmotion: [",
        #prompt="Read the following interaction, then pick just one of the most appropriate emotions to respond with to "+user+" as "+bot+" from this list only: [cheerful, empathetic, angry, sad, excited, friendly, terrified, shouting, unfriendly, whispering, hopeful].\n"+raspunsF+"\n"+user+": "+zice+"\n\nEmotion: [",
        temperature=0.0,
        max_tokens=12,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=[user+": ", bot+": ", "Emotion: [", ","],
    )
    return toneLabel

""" CHAT_GPT3()
1. inputs and reads user prompt
2. responds with given style from TONE_GPT3()
3. returns response
"""
def chat_gpt3(zice):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt= bot+" is speaking Spanish wih "+user+" Spanish."+context+"\n"+user+": "+zice+"\n"+bot+":",
        #prompt= "This is a conversation between "+bot+" and "+user+" in a Discord voice chat. "+bot+" leads the conversation by asking fun and interesting questions, and switches up the topic when things get boring. "+bot+" is witty, sarcastic, and brutally honest."+context+"\n"+user+": "+zice+"\n"+bot+" ["+style+"]:",
        temperature=1.0,
        max_tokens=256,
        top_p=1.0,
        frequency_penalty=2.0,
        presence_penalty=0.0,
        stop=[user+": ", bot+": ", "["],
        echo=False,
    )
    return response

""" TTS()
1. inputs response SSML from CHAT_GPT()
2. streams async synthesis
"""
def tts(ssml):
    global speech_synthesis_result
    speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml).get()

while (True):

    try:
        
        # controls whether interaction has been recieved and processed or not
        done = False
        
        # given input stt
        # generates style and response from GPT-3
        # synthesizes response tts
        def textSpeech(inp):
            
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
                print("NON-SILENCE")
                print(prompt)
                # gets style GPT would like to respond with
                #style = ((tone_gpt3(inp)).choices[0].text).split("]")[0]
                #print(style)
                # gets GPT text message response completion
                raspuns = (chat_gpt3(inp)).choices[0].text
                # formats raspuns
                #raspunsF = bot+" ["+style+"]: " + raspuns
                raspunsF = bot+": "+raspuns
                print(raspunsF)
                #print(raspuns)
                # concats message to memory/history
                context += "\n"+prompt+"\n"+raspunsF
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
                <mstts:express-as style="'''+style+'''" styledegree="1">
                '''+ raspuns +'''
                </mstts:express-as>
                </prosody>
                </voice>
                </speak>'''
                # synthesizes TTS with input SSML
                tts(xmlStringReg)
                # resets silence count to 0
                silenceCount = 0
                # marks interaction
                done = True
            # processes silent interaction
            else:
                # checks if user has been silent for certain amount of time
                if silenceCount == 2:
                    prompt = user+": ..."
                    print("SILENCE PROMPT")
                    print(prompt)
                    # gets style GPT would like to respond with
                    #style = ((tone_gpt3("...")).choices[0].text).split("]")[0]
                    #print(style)
                    # gets GPT text message response completion
                    raspuns = (chat_gpt3("...")).choices[0].text
                    # formats raspuns
                    raspunsF = bot+": "+raspuns
                    print(raspunsF)
                    # concats message to memory/history
                    context += "\n"+prompt+"\n"+raspunsF
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
                    tts(xmlStringReg)
                    # resets silence count to 0
                    silenceCount = 0
                    # marks interaction
                    done = True
                # increases silence count
                print("SILENCE")
                silenceCount += 1
        
        # listens for speech
        while not done:
            print("|||||||||| LISTENING ||||||||||")
            speech_recognition_result = speech_recognizer.recognize_once_async().get()
            speech_recognizer.recognized.connect(textSpeech(speech_recognition_result.text))
            
    except Exception as e:
        print("Could not understand", e)