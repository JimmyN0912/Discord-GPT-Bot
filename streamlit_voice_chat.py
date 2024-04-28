import streamlit as st
import requests
from audiorecorder import audiorecorder
import json
import base64
import os

# Variables
headers = {"Content-Type": "application/json"}
stt_url = "http://192.168.0.175:6000/speech2text"
ttt_url = "http://192.168.0.175:5000/v1/chat/completions"
tts_url = "http://192.168.0.175:6000/text2speech"
voice_chat_default = [
    {
        'role': 'user',
        'content': "You are a voice chat assistant who will generate responses based on the user's messages. Your responses will be transformed into voice messages and sent to the user. The following message is the user's message or question, please respond."
    },
    {
        'role': 'assistant',
        'content': "Ok."
    }]
voice_chat = voice_chat_default.copy()

st.set_page_config(page_title='Voice Chat Bot', page_icon='🤖', layout='wide')


st.title("Voice Chat Bot")
st.write("這是我的一個小技術展示的頁面，你可以用語音與AI對話。要使用此功能，請按下面的按鈕開始錄製語音。")
st.write("目前只支援英文語音轉文字，請用英文語音與AI對話。")

sidebar = st.sidebar
sidebar.title("Voice Chat Bot")
sidebar.subheader("使用注意事項：")
sidebar.text("1. 請用英文語音與AI對話。")
sidebar.text("2. 請按錄音按鈕開始錄製語音。")
sidebar.text("3. AI語音生成耗時較長，請耐心等待。")
sidebar.text("4. 請按提交按鈕提交語音，AI將生成回應。")
sidebar.text("5. 請按重製按鈕重置對話，重新開始。")
sidebar.text("6. 目前每次提交都是獨立的對話！")
sidebar.info("AI生成內容僅供展示，生成內容可能不準確，僅供參考。")

audio = audiorecorder("Click to record 按我來開始錄音", "Click to stop recording 按我來停止錄音")

if len(audio) > 0:
    # To play audio in frontend:
    st.audio(audio.export().read())  

    # To save audio to a file, use pydub export method:
    filename = "C:\\GPT-Bot\\streamlit_voice_chat\\input\\input.wav"
    audio.export(filename, format="wav")

    # To get audio properties, use pydub AudioSegment properties:
    # st.write(f"Frame rate: {audio.frame_rate}, Frame width: {audio.frame_width}, Duration: {audio.duration_seconds} seconds")

def get_text_from_audio():
    # Send audio to Speech-to-Text API
    with open("C:\\GPT-Bot\\streamlit_voice_chat\\input\\input.wav", "rb") as f:
        audio = f.read()
        base64_audio = base64.b64encode(audio).decode("utf-8")
    data = json.dumps({'file': base64_audio})
    print("Sending audio to Speech-to-Text API")
    response = requests.post(stt_url, headers=headers, data=data, timeout=180)
    return response.json()["text"]

def get_text_to_text(text):
    # Send text to Text-to-Text API
    voice_chat.append({'role': 'user', 'content': text})
    data = {
        "mode": "instruct",
        "messages": voice_chat,
        "max_tokens": 512,
        "temperature": 0.5
    }
    print("Sending text to Text-to-Text API")
    response = requests.post(ttt_url, headers=headers, json=data, timeout=300)
    voice_chat.append({'role': 'assistant', 'content': response.json()["choices"][0]["message"]["content"]})
    return response.json()["choices"][0]["message"]["content"]

def get_audio_from_text(text):
    # Send text to Text-to-Speech API
    data = {'prompt': text}
    print("Sending text to Text-to-Speech API")
    response = requests.post(tts_url, headers=headers, json=data, timeout=300)
    filename = "C:\\GPT-Bot\\streamlit_voice_chat\\output\\response.wav"  
    with open(filename, "wb") as f:
        f.write(response.content)
    return filename

if st.button("Submit 提交"):
    status_bar = st.progress(0, "Recognizing speech from recording... 識別錄音中...")
    text = get_text_from_audio()
    status_bar.progress(0.33, "Recognition complete. Generating response... 識別完成，生成回應中...")
    response = get_text_to_text(text)
    status_bar.progress(0.66, "Response generated. Generating voice message... 回應生成完畢，生成語音中...")
    filename = get_audio_from_text(response)
    status_bar.progress(1.0, "Voice message generated. Playback below: 語音生成完畢，以下是語音回應：")
    st.audio(filename, format='audio/wav')
    st.write(response)

if st.button("Reset 重置"):
    voice_chat = voice_chat_default.copy()
    if os.path.exists("C:\\GPT-Bot\\streamlit_voice_chat\\input\\input.wav"):
        os.remove("C:\\GPT-Bot\\streamlit_voice_chat\\input\\input.wav")
    if os.path.exists("C:\\GPT-Bot\\streamlit_voice_chat\\output\\response.wav"):
        os.remove("C:\\GPT-Bot\\streamlit_voice_chat\\output\\response.wav")
    st.rerun()
