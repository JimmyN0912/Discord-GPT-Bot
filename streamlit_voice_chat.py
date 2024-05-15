import streamlit as st
import requests
from st_audiorec import st_audiorec
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
        'content': "You are a voice chat assistant who will generate responses based on the user's messages. Your responses will be transformed into voice messages and sent to the user. The following message is the user's message or question, please respond. Please keep your response short and concise. Thank you!",
        'voice_message': None
    },
    {
        'role': 'assistant',
        'content': "Ok.",
        'voice_message': None
    }]
if "voice_chat" not in st.session_state:
    st.session_state.voice_chat = voice_chat_default.copy()

st.set_page_config(page_title='Voice Chat Bot', page_icon='🤖', layout='wide')


st.title("Voice Chat Bot")
st.header("New Updates 新功能更新")
st.write("2024-04-29: 新增了長篇對話功能，現在可以接續對話！")
st.markdown("---")

sidebar = st.sidebar
sidebar.title("Voice Chat Bot")
sidebar.subheader("關於本頁面：")
sidebar.text("這是我的一個小技術展示的頁面，\n你可以用語音與AI對話。\n要使用此功能，請按下面的按鈕開始錄製語音。")
sidebar.text("目前只支援英文語音轉文字，請用英文語音與AI對話。")
sidebar.subheader("使用注意事項：")
sidebar.text("1. 請用英文語音與AI對話。")
sidebar.text("2. 請按錄音按鈕開始錄製語音。")
sidebar.text("3. AI語音生成耗時較長，請耐心等待。")
sidebar.text("4. 請按提交按鈕提交語音，AI將生成回應。")
sidebar.text("5. 請按重製按鈕重置對話，重新開始。")
sidebar.info("AI生成內容僅供展示，生成內容可能不準確，僅供參考。", icon="🚨")


st.subheader("Voice Chat 語音對話區")
st.info("The chat history will be displayed here. 您的對話紀錄將顯示在這裡。", icon="📝")
for message in st.session_state.voice_chat[2:]:
    if message["role"] == "user":
        st.markdown(f"<div style='text-align: right; width: 50%; margin-left: 50%; padding: 10px; border: 1px solid black; border-radius: 15px; background-color: #CECECE; color: black'>User: {message['content']}</div>", unsafe_allow_html=True)
        if message["voice_message"] is not None:
            audio_html = f'<audio controls style="margin-left: 50%;"><source src="data:audio/wav;base64,{message["voice_message"]}" type="audio/wav"></audio>'
            st.markdown(audio_html, unsafe_allow_html=True)
    elif message["role"] == "assistant":
        st.markdown(f"<div style='text-align: left; width: 50%; padding: 10px; border: 1px solid black; border-radius: 15px; background-color: #CECECE; color: black'>Assistant: {message['content']}</div>", unsafe_allow_html=True)
        if message["voice_message"] is not None:
            audio_html = f'<audio controls style="margin-left: 50%;"><source src="data:audio/wav;base64,{message["voice_message"]}" type="audio/wav"></audio>'
            st.markdown(audio_html, unsafe_allow_html=True)

st.markdown("---")
st.subheader("Voice Recording 語音錄製區")
st.info("Press the button below to start recording your voice. 按下面的按鈕開始錄製您的語音。", icon="🎤")

wav_audio_data = st_audiorec()

st.warning("Please only press submit after you have recorded your voice. 請在錄製完語音後再按提交。")

def get_text_from_audio():
    # Send audio to Speech-to-Text API
    base64_audio = base64.b64encode(wav_audio_data).decode("utf-8")
    st.session_state.voice_chat.append({'role': 'user', 'content': None, 'voice_message': base64_audio})
    data = json.dumps({'file': base64_audio})
    print("Sending audio to Speech-to-Text API")
    response = requests.post(stt_url, headers=headers, data=data, timeout=180)
    print(response.json()["text"])
    return response.json()["text"]

def get_text_to_text(text):
    # Send text to Text-to-Text API
    st.session_state.voice_chat[-1]['content'] = text
    messages = [{'role': message['role'], 'content': message['content']} for message in st.session_state.voice_chat]
    data = {
        "mode": "instruct",
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.5
    }
    print("Sending text to Text-to-Text API")
    response = requests.post(ttt_url, headers=headers, json=data, timeout=300)
    st.session_state.voice_chat.append({'role': 'assistant', 'content': response.json()["choices"][0]["message"]["content"], 'voice_message': None})
    print(response.json()["choices"][0]["message"]["content"])
    return response.json()["choices"][0]["message"]["content"]

def get_audio_from_text(text):
    # Send text to Text-to-Speech API
    data = {'prompt': text}
    print("Sending text to Text-to-Speech API")
    response = requests.post(tts_url, headers=headers, json=data, timeout=300)
    filename = "C:\\GPT-Bot\\streamlit_voice_chat\\output\\response.wav"  
    with open(filename, "wb") as f:
        f.write(response.content)
        st.session_state.voice_chat[-1]['voice_message'] = base64.b64encode(response.content).decode("utf-8")
    return response.content

if st.button("Submit 提交"):
    status_bar = st.progress(0, "Recognizing speech from recording... 識別錄音中...")
    text = get_text_from_audio()
    status_bar.progress(0.33, "Recognition complete. Generating response... 識別完成，生成回應中...")
    response = get_text_to_text(text)
    status_bar.progress(0.66, "Response generated. Generating voice message... 回應生成完畢，生成語音中...")
    get_audio_from_text(response)
    status_bar.progress(1.0, "Voice message generated. Playback below: 語音生成完畢，以下是語音回應：")
    st.rerun()

if st.button("Reset 重置"):
    st.session_state.voice_chat = voice_chat_default.copy()
    if os.path.exists("C:\\GPT-Bot\\streamlit_voice_chat\\input\\input.wav"):
        os.remove("C:\\GPT-Bot\\streamlit_voice_chat\\input\\input.wav")
    if os.path.exists("C:\\GPT-Bot\\streamlit_voice_chat\\output\\response.wav"):
        os.remove("C:\\GPT-Bot\\streamlit_voice_chat\\output\\response.wav")
    st.rerun()
