import os
import pyaudio
from openai import OpenAI

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 2048
WAVE_OUTPUT_FILENAME = "/Users/simonprivat/Workspace/Projects/emo-consens-bot/bot_system/output.wav"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
