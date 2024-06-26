import discord
import requests
import nest_asyncio
import datetime
import logging
import os
import colorama
import time
from collections import defaultdict
import httpx
import asyncio
from dotenv import load_dotenv
import base64
from PIL import Image
import io
from flask import Flask, jsonify, request
import threading
from waitress import serve
import google.generativeai as genai
import pickle
import aiofiles
import cohere
from concurrent.futures import ThreadPoolExecutor
from functools import partial

nest_asyncio.apply()
load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
google_api_key = os.getenv('GOOGLE_API_KEY')
cohere_api_key = os.getenv('COHERE_API_KEY')
genai.configure(api_key=google_api_key)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

#Set up directories
main_dir = 'C:\\GPT-Bot'
sub_dirs = ['logs', 'context', 'images', 'image_prompts', 'videos', 'video_prompts', 'music', 'music_prompts']

dirs = {}
for dir in sub_dirs:
    path = os.path.join(main_dir, dir)
    os.makedirs(path, exist_ok=True)
    dirs[dir] = path

log_dir = dirs['logs']
context_dir = dirs['context']
image_dir = dirs['images']
image_prompt_dir = dirs['image_prompts']
video_dir = dirs['videos']
video_prompt_dir = dirs['video_prompts']
music_dir = dirs['music']
music_prompt_dir = dirs['music_prompts']

#Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logging.addLevelName(logging.DEBUG, 'DEBG')

#Setup handlers
stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler(log_dir + '\GPT-Bot.log', "a", "utf-8")
stream_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

#setup logging formats
stream_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
stream_handler.setFormatter(stream_format)
file_handler.setFormatter(file_format)

#adding handlers
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

#Process names:
    # main.startup
    # main.testsvc
    # main.setdebg
    # main.setprse
    # message.recv
    # message.proc
    # message.send
    # reply.status
    # reply.llmsvc
    # reply.parser
    # reply.ngcsvc
    # reply.ngcctx
    # reply.ctxexp
    # reply.llmctx
    # reply.ngcimg
    # reply.lclimg
    # model.loader
    # reply.gemini
    # reply.persna
    # reply.imgvid

class ChatBot(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.online = True

        #Logger Setup
        self.logger = logger

        #Variables
        self.version = "23"
        self.version = "23.1"
        self.version_date = "2024.6.4"

        #Startup messages
        self.log("info", "main.startup", f"Discord Bot V{self.version} ({self.version_date}).")
        self.log("info", "main.startup", "Discord Bot system starting...")

        if os.path.exists(main_dir + "/response_count.pkl") and os.path.getsize(main_dir + "/response_count.pkl") > 0:
            self.log("debug", "main.startup", "Loading response count from file.")
            with open(main_dir + "/response_count.pkl", 'rb') as f:
                self.response_count = pickle.load(f)
            self.log("debug", "main.startup", "Response count loaded from file.")
        else:
            self.log("debug", "main.startup", "Response count file not found, setting to default values.")
            self.response_count = {
                "text": 0,
                "image": 0,
                "video": 0,
                "music": 0,
                "gemini": 0
            }
            self.log("debug", "main.startup", "Response count set to default values.")
        self.start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.start_time_timestamp = datetime.datetime.now().timestamp()
        self.log("info", "main.startup", f"start_time_timestamp generated: {self.start_time_timestamp}.")
        self.log("debug", "main.startup", f"start_time generated: {self.start_time}.")
        self.weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        #Settings
        self.log("debug", "main.startup", "Setting up bot settings and global variables.")
        self.ai_text_service_online = None
        self.ai_image_service_online = None
        self.ai_inference_server_online = None
        self.debug_log = 1
        self.headers = {"Content-Type": "application/json"}
        self.ai_text_service_context_url = "http://192.168.0.175:5000/v1/chat/completions"
        self.ai_image_service_url = "http://192.168.0.175:7861/sdapi/v1/txt2img"
        self.ai_inference_server_url = "http://192.168.0.175:6000"
        self.ai_model = None
        self.request_successful = None
        self.ai_tokens = 1024
        self.ai_temperature = 0.5
        self.load_model_args = defaultdict(lambda: {"cpu": True})
        self.load_model_args.update({
            "Mistral-7B-Instruct-v0.2-Quantised.gguf": {
                "cpu": False,
                "n_gpu_layers": 35
            },
            "Llama-2-7B-Quantised.gguf": {
                "cpu": False,
                "n_gpu_layers": 35
            },
            "Llama-2-13B-Quantised.gguf": {
                "cpu": False,
                "n_gpu_layers": 43
            },
            "Zephyr-7B-Quantised.gguf": {
                "cpu": False,
                "n_gpu_layers": 35
            },
            "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf": {
                "cpu": False,
                "n_gpu_layers": 33
            }
        })
        self.gemini_text_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        self.gemini_vision_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        self.image = None
        self.cohere_client = cohere.Client(api_key=cohere_api_key)
        self.log("debug", "main.startup", "Bot settings and global variables set.")

        #Message Histories
        self.log("debug", "main.startup", "Setting up default message histories.")
        self.context_messages_default = [
            {
                "role": "user",
                "content": "You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are coded with Python line by line by jimmyn3577, aims to help the user with anything they need, no matter the conversation is formal or informal.\nYou currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond."
            },
            {
                "role": "assistant",
                "content": "Ok."
            }
        ]
        self.context_messages_gemini_default = [
            {
                'role': 'user',
                'parts': ["You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are coded with Python line by line by jimmyn3577, aims to help the user with anything they need, no matter the conversation is formal or informal.\nYou currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond."]
            },
            {
                'role': 'model',
                'parts': ["Ok."]
            }]
        self.context_messages_gemini_default_token_count = sum(genai.count_message_tokens(prompt=message['parts'])['token_count'] for message in self.context_messages_gemini_default)
        self.context_messages_cohere_default = [
            {
                "role": "USER",
                "message": "You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are coded with Python line by line by jimmyn3577, aims to help the user with anything they need, no matter the conversation is formal or informal.\nYou currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond."
            },
            {
                "role": "CHATBOT",
                "message": "Ok."
            }
        ]
        self.personality_ai_mode = "Gemini"
        self.text_adventure_game_default = [
            {
                "role": "user",
                "content": "You are a text adventure game guide who will play a text adventure game with the user. Users call you by<@1086616278002831402>. You will guide the user through the game, and the user will say what they want to do in the game. You will then respond to the user's actions and provide action options to continue the game. When the user says 'Let's go!, or something similar, you will start the game. If the user want to play a game they provide, you will start the game based on the user's request. You will only generate text that is related to the game, and you will not generate actions for the user. You will use any language the user initially uses. The following is an example."
            },
            {
                "role": "assistant",
                "content": "Ok."
            },
            {
                "role": "user",
                "content": "Example:{A description of the surroundings and the environment, please be creative! Prompt thee user with action options:\n- Option 1\n- Option 2\n- Option 3}"
            },
            {
                "role": "assistant",
                "content": "Ok."
            }
        ]
        self.text_adventure_game_gemini_default = [
            {
                'role': 'user',
                'parts': ["You are a text adventure game guide who will play a text adventure game with the user. Users call you by<@1086616278002831402>. You will guide the user through the game, and the user will say what they want to do in the game. You will then respond to the user's actions and provide action options to continue the game. When the user says 'Let's go!, or something similar, you will start the game. If the user want to play a game they provide, you will start the game based on the user's request. You will only generate text that is related to the game, and you will not generate actions for the user. You will use any language the user initially uses. The following is an example."]
            },
            {
                'role': 'model',
                'parts': ["Ok."]
            },
            {
                'role': 'user',
                'parts': ["Example:{A description of the surroundings and the environment, please be creative! Prompt thee user with action options:\n- Option 1\n- Option 2\n- Option 3}"]
            },
            {
                'role': 'model',
                'parts': ["Ok."]
            }]
        self.story_writer_default = [
            {
                "role": "user",
                "content": "You are a story writer who will write a story based on the user's prompt. Users call you by<@1086616278002831402>. You will write a story based on the user's prompt, and the user will provide the prompt for the story. You will then write the story based on the user's prompt and provide the story to the user. You will only generate text that is related to the story, and you will not generate actions for the user. You will use any language the user initially uses. Character names can be freely decided by the user, even user ids."                
            },
            {
                "role": "assistant",
                "content": "Ok."
            }
        ]
        self.story_writer_gemini_default = [
            {
                'role': 'user',
                'parts': ["You are a story writer who will write a story based on the user's prompt. Users call you by<@1086616278002831402>. You will write a story based on the user's prompt, and the user will provide the prompt for the story. You will then write the story based on the user's prompt and provide the story to the user. You will only generate text that is related to the story, and you will not generate actions for the user. You will use any language the user initially uses. Character names can be freely decided by the user, even user ids."]
            },
            {
                'role': 'model',
                'parts': ["Ok."]
            }]
        self.log("debug", "main.startup", "Default message histories initialized.")

        #Load message histories from files
        self.log("debug", "main.startup", "Loading message histories from files.")
        self.context_messages = self.load_variables("/context_messages_local.pkl")
        self.context_messages_modified = self.load_variables("/context_messages_local_modified.pkl")
        self.context_messages_cohere = self.load_variables("/context_messages_cohere.pkl")
        self.context_messages_cohere_used = self.load_variables("/context_messages_cohere_used.pkl")
        self.user_image_creations = self.load_variables("/user_image_creations.pkl")
        self.context_messages_gemini = self.load_variables("/context_messages_gemini.pkl")
        self.context_messages_gemini_used = self.load_variables("/context_messages_gemini_used.pkl")
        self.text_adventure_game = self.load_variables("/text_adventure_game.pkl")
        self.story_writer = self.load_variables("/story_writer.pkl")
        self.text_adventure_game_gemini = self.load_variables("/text_adventure_game_gemini.pkl")
        self.story_writer_gemini = self.load_variables("/story_writer_gemini.pkl")
        self.log("debug", "main.startup", "Message histories loaded from files.")
        self.log("info", "main.startup", "Connecting to Discord...")

    #Logging Function
    def log(self, lvl, service, log_message):
        log_method = getattr(logger, lvl, None)
        color = colorama.Fore.WHITE
        if service == "main.setdebg":
            color = colorama.Fore.RED
        elif service == "message.recv" or service == "message.proc" or service == "message.send":
            color = colorama.Fore.LIGHTYELLOW_EX
        elif service == "reply.parser":
            color = colorama.Fore.LIGHTBLUE_EX
        elif service == "reply.llmsvc" or service == "reply.llmctx" or service == "reply.lclimg":
            color = colorama.Fore.LIGHTMAGENTA_EX
        elif service == "reply.ngcsvc" or service == "reply.ngcctx" or service == "reply.ngcimg":
            color = colorama.Fore.GREEN
        elif service == "reply.gemini":
            color = colorama.Fore.LIGHTCYAN_EX
        if log_method is not None:
            log_message = log_message.encode('utf-8').decode('utf-8')
            log_method(f"{color}{service}{colorama.Style.RESET_ALL}    {log_message}")
        else:
            self.logger.error(f"Invalid log level: {lvl}")

    # Discord.py module startup message
    async def on_ready(self):
        self.bot_id = self.user.id
        self.log("debug", "main.startup", f"Bot ID: {self.bot_id}.")
        self.log("info", "main.startup", "Connection to Discord established successfully.")
        await self.presence_update("idle")
        #Testing AI system status
        service_check_task = asyncio.create_task(self.auto_service_check())
    
    # Receiving messages
    async def on_message(self, message):
        #Ignore when bot is set as offline
        if self.online == False:
            return

        #Actions if message comes from bot
        if message.author == self.user:
            self.log("debug", "message.recv", "Message received. Author is Bot, ignoring message.")
            return

        #Announcing message
        self.log("info", "message.recv", f"Message Received: '{message.content}', from {message.author.name}, in {message.guild.name} / {message.channel.category.name} / {message.channel}.")
        self.log("debug", "message.recv", f"Message ID: {message.id}. Message Replying: {message.reference}. Message attachments: {message.attachments}.")
            
        #Actions if bot isn't mentioned in message
        if f'<@1086616278002831402>' not in message.content:
            self.log("info", "message.recv", "Bot not mentioned in message, ignoring message.")
            return
        
        #Rejecting messages in Chatting-聊天區
        if message.channel.category.name == 'Chatting-聊天區':
            self.log("info", "message.proc", "Message is in Chatting-聊天區, rejecting message.")
            await message.channel.send("Please use other channels for chatting with the bot.\n請使用其他頻道與機器人聊天。")
            return
        

        #Generating AI Response
        #Handling image attachments
        if message.attachments:
            for attachment in message.attachments:
                self.log("info", "message.proc", "Attachment detected, checking file type.")
                if attachment.filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.PNG', '.JPG', '.JPEG', '.GIF', '.BMP')):
                    self.log("info", "message.proc", "Image file detected, downloading image.")
                    request = requests.get(attachment.url)
                    self.log("info", "message.proc", "Image downloaded. Saving image.")
                    self.image = Image.open(io.BytesIO(request.content))
                    self.image_bytes = request.content
                    self.image.save("C:\GPT-Bot\image.png")
                    self.log("info", "message.proc", "Image saved.")

        #Text to Image Generation
        if message.channel.category.name == 'text-to-image':
            self.log("info", "message.proc", "Message is in text-to-image, starting image generation process.")
            init_message = await message.channel.send("Generating image...")
            if self.ai_image_service_online == True:
                self.log("info", "message.proc", "Bot text-to-image services online. Starting reply.lclimg process.")
                image = await self.ai_response_image(message, init_message)
            else:
                self.log("info", "message.proc", "Bot text-to-image services deactivated. Rejecting message.")
                await init_message.delete()
                await message.channel.send("Text-to-image services are currently offline. Please try again later.")
                return
            if self.request_successful == False:
                self.request_successful = None
                return
            self.log("info", "message.proc", "Image generated. Sending image.")
            image = discord.File(fp=image, filename="image.png")
            embed = discord.Embed(color=int('FE9900', 16))
            embed.add_field(name="Prompt", value=message.content.split(' ', 1)[1], inline=False)
            embed.add_field(name="Images generated by you:", value=self.user_image_creations[message.author.name], inline=False)
            if self.ai_image_service_online == True:
                embed.set_footer(text=f"Model used: Fluently-V1 | AI-Chat V{self.version}")
            else:
                embed.set_footer(text=f"Model used: SDXL | AI-Chat V{self.version}")
            embed.set_image(url="attachment://image.png")
            embed.timestamp = datetime.datetime.now()
            await init_message.delete()
            await message.channel.send(file=image,embed=embed)
            # send image
            self.log("info", "message.send", "Image sent.")
            return
        
        #Text to Music Generation
        if message.channel.category.name == 'text-to-music':
            self.log("info", "message.proc", "Message is in text-to-music, starting music generation process.")
            init_message = await message.channel.send("Generating music...")
            if self.ai_inference_server_online == True:
                music = await self.ai_response_music(message, init_message)
                self.log("info", "message.proc", "Music generated. Sending music.")
                music_file = discord.File(fp=music, filename="music.wav")
                await init_message.delete()
                await message.channel.send(file=music_file)
                self.log("info", "message.send", "Music sent.")
                return
            else:
                self.log("info", "message.proc", "Bot inference server responses deactivated. Rejecting message.")
                await init_message.delete()
                await message.channel.send("Text-to-music services are currently offline. Please try again later.")
                return
            
        #Text to Video Generation
        if message.channel.category.name == 'text-to-video':
            self.log("info", "message.proc", "Message is in text-to-video, starting video generation process.")
            init_message = await message.channel.send("Generating video...")
            if self.ai_inference_server_online == True:
                video = await self.ai_response_video(message, init_message)
                self.log("info", "message.proc", "Video generated. Sending video.")
                video_file = discord.File(fp=video, filename="video.gif")
                await init_message.delete()
                await message.channel.send(file=video_file)
                self.log("info", "message.send", "Video sent.")
                return
            else:
                self.log("info", "message.proc", "Bot inference server responses deactivated. Rejecting message.")
                await init_message.delete()
                await message.channel.send("Text-to-video services are currently offline. Please try again later.")
                return

        message_to_edit = await message.channel.send(f"Generating response...")
        message_user_id = message.author.id
        message_channel_id = message.channel.id    

        #Google Gemini Generation
        if message.channel.category.name == 'google-gemini':
            self.log("info", "message.proc", "Message is in google-gemini, starting reply.gemini process.")
            context = True if message.channel.name == 'context' else False
            self.log("debug", "message.proc", f"Context: {context}.")
            response = await self.ai_response_gemini(message, context, message_user_id, message_to_edit, self.image)
            if response != None:
                if self.image == None:
                    await message_to_edit.edit(content="Model Used: Google Gemini 1.5 Flash")
                    await self.send_message(message,response)
                    self.image = None
                    return
                else:
                    await message_to_edit.edit(content="Model Used: Google Gemini 1.5 Pro")
                    await self.send_message(message,response)
                    self.image = None
                    return
            else:
                return
        
        #Personality AI Text Generation
        if message.channel.category.name == 'text-adventure':
            response = await self.personality_ai_request(message, message_channel_id, message_to_edit, "text-adventure")
            await message_to_edit.delete()
            await self.send_message(message,response)
            return
        
        if message.channel.category.name == 'story-writer':
            response = await self.personality_ai_request(message, message_channel_id, message_to_edit, "story-writer")
            await message_to_edit.delete()
            await self.send_message(message,response)
            return
        
        #Cohere Command R+ Text Generation
        if message.channel.category.name == 'text-to-text-search':
            context = True if message.channel.name == 'context' else False
            start_time = time.time()
            response, cited_reponse, docs = await self.ai_response_cohere(message, context, message_user_id, message_to_edit)
            end_time = time.time()
            time_taken = end_time - start_time
            await message_to_edit.edit(content="Model Used: Cohere Command R+")
            await self.send_message(message,response)
            if docs != None:
                # Sort docs by 'id'
                docs = sorted(docs, key=lambda k: k['id'])
                citations = ""
                for doc in docs:
                    citations += f"ID: {doc['id']},\nTitle: {doc['title']},\nURL: {doc['url']}\n\n"
                cited_response_message = f"參考資料使用位置:\n{cited_reponse}"
                await self.send_message(message,cited_response_message)
                embed = discord.Embed(color=int('FE9900', 16))
                embed.add_field(name="參考資料", value=citations, inline=False)
                await message.channel.send(embed=embed)
            return

        #Normal AI Text Generation
        if message_user_id not in self.context_messages:
            self.context_messages[message_user_id] = self.context_messages_default.copy()
        if message_user_id not in self.context_messages:
            self.context_messages[message_user_id] = self.context_messages_default.copy()
        if message_user_id not in self.context_messages_modified:
            self.context_messages_modified[message_user_id] = False
        if message_user_id not in self.context_messages_modified:
            self.context_messages_modified[message_user_id] = False

        if self.ai_text_service_online == True:
            context = True if message.channel.name == 'context' else False
            if context == True:
                self.log("info", "message.proc", "Starting reply.llmctx process.")
            else:
                self.log("info", "message.proc", "Starting reply.llmsvc process.")
            response, model_used = await self.ai_request(message, message_to_edit, context, message_user_id)
            self.log("info", "message.send", "Sending message.")
            await message_to_edit.edit(content=f"*Model Used: {model_used}*")
            self.log("info", "message.send", f"Message sent. AI model used: {model_used}.")
            await self.send_message(message, response)

        else:
            self.log("info", "message.proc", "Bot text-to-text services deactivated. Rejecting message.")
            await message_to_edit.delete()
            await message.channel.send("Text-to-text services are currently offline. Please try again later.")

    #Generating AI Response
    async def ai_request(self, message, message_to_edit, context, message_user_id): 
        await self.presence_update("ai")

        ### Generating AI Request ###
        service = "reply.llmsvc" if context == False else "reply.llmctx"
        self.log("info", service, "Generating AI request.")
        #Set max tokens
        max_tokens = self.ai_tokens
        self.log("debug", service, f"AI max tokens: {max_tokens}.")
        #Generate request headers
        headers = self.headers
        self.log("debug", service, f"AI request headers generated: {headers}.")
        if context == True:
            #Set request URL
            url = self.ai_text_service_context_url
            self.log("debug", service, f"AI request URL: {url}.")
            if self.context_messages_modified[message_user_id] == False:
                current_date_formatted, weekday = self.get_weekday()
                prompt = f"Today is {current_date_formatted}, which is {weekday}. The user's id is <@{message.author.id}>, and their message is: {message.content}."
                self.context_messages[message_user_id].append({
                    "role": "user",
                    "content": prompt
                })
                self.context_messages_modified[message_user_id] = True
            else:
                self.context_messages[message_user_id].append({
                    "role": "user",
                    "content": message.content
                })
            self.log("debug", service, "Message history updated.")
            #Combine request data
            data = {
                "mode": "instruct",
                "messages": self.context_messages[message_user_id],
                "max_tokens": self.ai_tokens,
                "temperature": self.ai_temperature
            }
        else:
            #Set request URL
            url = self.ai_text_service_context_url
            self.log("debug", service, f"AI request URL: {url}.")
            current_date_formatted, weekday = self.get_weekday()
            #Generating AI Prompt
            ai_prompt = self.context_messages_default.copy()
            ai_prompt.append({
                "role": "user",
                "content": message.content
            })
            self.log("debug", service, f"AI Prompt generated.")
            #Combine request data
            data = {
                "mode": "instruct",
                "messages": ai_prompt,
                "max_tokens": self.ai_tokens,
                "temperature": self.ai_temperature
            }
        self.log("debug", service, f"AI request data generated.")
        self.log("info", service, "AI request generated, sending request.")
        update_task = asyncio.create_task(self.update_time(message_to_edit))
        i = 1
        for _ in range(5):
            try:
                async with httpx.AsyncClient(verify=False,timeout=300) as client:
                    response = await client.post(url, headers=headers, json=data)
                    self.request_successful = True
                    break
            except httpx.HTTPStatusError:
                if i == 5:
                    self.log("error", service, "AI request failed, for the fifth time. Raising error.")
                    await message.channel.send(f"AI request failed.\nError code: {response.status_code}.\nError text: {response.text}.")
                    update_task.cancel()
                    self.request_successful = False
                    await self.presence_update("idle")
                    self.log("info", service, "reply.llmsvc process exit.")
                    return
                self.log("error", service, f"AI request failed, Error code: {response.status_code}.")
                self.log("error", service, f"AI request failed, Error text: {response.text}.")
                self.log("debug", service, "Retrying AI request.")
                time.sleep(5)
                i += 1
        self.log("info", service, "AI response received, start parsing.")
        update_task.cancel()
        await message_to_edit.edit(content="AI response received, processing response...")
        self.log("info", service, "reply.llmsvc process exit.")
        self.log("info", "message.proc", "Starting reply.parser process.")

        ### Parsing AI Response ###
        self.log("info", "reply.parser", "Parsing AI response.")
        if response.status_code != 200:
            self.log("error", "reply.parser", f"AI response status code: {response.status_code}.")
            self.log("error", "reply.parser", f"AI response text: {response.text}.")
            await self.presence_update("idle")
            self.log("info", "reply.parser", "AI response parsing complete. Reply.parse exit.")
            return
        assistant_response = response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        if context == True:
            self.context_messages[message_user_id].append({
                "role": "assistant",
                "content": assistant_response
            })
            self.log("debug", "reply.parser", "Message history updated.")
        #Extracting AI model used
        model_used = response.json()['model']
        self.log("debug", "reply.parser", f"AI model used: {model_used}")
        self.ai_model = model_used
        #Extracting AI prompt tokens
        prompt_tokens = response.json()['usage']['prompt_tokens']
        self.log("debug", "reply.parser", f"AI prompt tokens: {prompt_tokens}")
        #Extracting AI predict tokens
        completion_tokens = response.json()['usage']['completion_tokens']
        self.log("debug", "reply.parser", f"AI predict tokens: {completion_tokens}")
        self.response_count["text"] += 1
        await self.presence_update("idle")
        self.log("info", "reply.parser", "AI response parsing complete. Reply.parse exit.")

        return assistant_response, model_used
 
    #Get next filename (for context export)
    def get_next_filename(self, directory, base_filename, file_extension):
        i = 1
        while True:
            filename = f"{directory}/{base_filename}-{i}.{file_extension}"
            if not os.path.exists(filename):
                return filename
            i += 1

    #Edit Message
    async def send_message(self,message,assistant_response):
        try:
            await message.channel.send(assistant_response)
        except discord.errors.HTTPException as e:
            if e.code == 50035:
                chunks = [assistant_response[i:i+2000] for i in range(0, len(assistant_response), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                raise

    #Change Bot Presence
    async def presence_update(self,activity):
        if activity == 'idle':
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="the waiting game."))
            self.log("debug", "main.setprsc", "Bot presence set to 'Playing the waiting game'.")
        elif activity == 'status':
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the status report."))
            self.log("debug", "main.setprsc", "Bot presence set to 'Streaming the status report'.")
        elif activity == 'ai':
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name="AI data."))
            self.log("debug", "main.setprsc", "Bot presence set to 'Streaming AI data'.")

    #Update Time
    async def update_time(self,message_to_edit):
        elapsed_time = 0
        while True:
            await message_to_edit.edit(content=f"Request sent, waiting for server response. Time elapsed: {elapsed_time} seconds.")
            elapsed_time += 1
            await asyncio.sleep(1)

    def get_weekday(self):
            current_date = datetime.datetime.now()
            current_date_formatted = current_date.strftime('%Y-%m-%d')
            weekday = self.weekday_names[current_date.weekday()]
            return current_date_formatted, weekday

    #Generate AI Response - Image 
    async def ai_response_image(self, message, init_message):
        await self.presence_update("ai")
        self.log("info", "reply.lclimg", "AI image prompt received. Generating AI image.")
        url = self.ai_image_service_url
        prompt = message.content.split(' ', 1)[1]
        self.log("debug", "reply.lclimg", f"AI prompt: {prompt}.")
        payload = {
            "prompt": prompt,
            "steps": 20,
            "cfg_scale": 7,
            "seed": -1
        }
        self.log("info", "reply.lclimg", "AI request generated, sending request.")
        await init_message.edit(content="Image generation request sent, waiting for AI response...")
        response = requests.post(url=url, json=payload)
        self.log("info", "reply.lclimg", "AI response received, start parsing.")
        await init_message.edit(content="AI image generation complete, processing results...")
        image = Image.open(io.BytesIO(base64.b64decode(response.json()['images'][0])))
        # save image
        filename = self.get_next_filename(image_dir, 'image', 'png')
        image.save(filename)
        filename_prompt = self.get_next_filename(image_prompt_dir, 'image-prompt', 'txt')
        with open(filename_prompt, 'w', encoding='utf-8') as f:
            f.write(f"Image prompt: {prompt}")
        self.log("info", "reply.lclimg", "AI image response parsing complete. Reply.lclimg exit.")
        self.log("info", "reply.lclimg", "Image saved.")
        self.response_count["image"] += 1
        if message.author.name not in self.user_image_creations:
            self.user_image_creations[message.author.name] = 0
        self.user_image_creations[message.author.name] += 1
        await self.presence_update("idle")
        return filename
    
    #Check local service status
    async def service_check(self):
        #Testing AI system status
        self.log("debug", "main.testsvc", "Testing AI text system status.")
        for _ in range(5):
            try:
                test_query = requests.get("http://192.168.0.175:5000/v1/models", timeout=3, headers={"Content-Type": "application/json"})
                if test_query.status_code == 200:
                    self.ai_text_service_online = True
                    self.log("info", "main.testsvc", "Local AI text service is online, bot text-to-text responses activated.")
                    break
            except requests.exceptions.ConnectionError:
                # Deactivate bot text-to-text responses
                self.ai_text_service_online = False
                self.log("info", "main.testsvc", "Local AI service is offline, bot text-to-text responses deactivated.")
                break
            except Exception as e:
                self.log("error", "main.testsvc", f"An unexpected error occurred: {str(e)}. Retrying.")
                time.sleep(10)
        
        self.log("debug", "main.testsvc", "Testing AI image system status.")
        for _ in range(5):
            try:
                test_query = requests.get("http://192.168.0.175:7861/internal/ping", timeout=3, headers={"Content-Type": "application/json"})
                if test_query.status_code == 200:
                    self.ai_image_service_online = True
                    self.log("info", "main.testsvc", "Local AI image service is online, bot text-to-image responses activated.")
                    break
            except requests.exceptions.ConnectionError:
                # Deactivate bot text-to-image responses
                self.ai_image_service_online = False
                self.log("info", "main.testsvc", "Local AI image service is offline, bot text-to-image responses deactivated.")
                break
            except Exception as e:
                self.log("error", "main.testsvc", f"An unexpected error occurred: {str(e)}. Retrying.")
                time.sleep(10)
        
        self.log("info", "main.testsvc", "Testing AI inference server status.")
        for _ in range(5):
            try:
                test_query = requests.get(self.ai_inference_server_url + "/status", timeout=3, headers={"Content-Type": "application/json"})
                if test_query.status_code == 200:
                    self.ai_inference_server_online = True
                    self.log("info", "main.testsvc", "Local AI inference server is online, bot inference server responses activated.")
                    break
            except requests.exceptions.ConnectionError:
                # Deactivate bot text-to-music responses
                self.ai_inference_server_online = False
                self.log("info", "main.testsvc", "Local AI inference server is offline, bot inference server responses deactivated.")
                break
            except Exception as e:
                self.ai_inference_server_online = False
                self.log("error", "main.testsvc", f"An unexpected error occurred: {str(e)}. Retrying.")
                time.sleep(10)

    #Auto Check Service Status
    async def auto_service_check(self):
        while True:
            self.log("info", "main.testsvc", "Auto service check started.")
            await self.service_check()
            self.log("info", "main.testsvc", "Auto service check complete.")
            await asyncio.sleep(600)

    #Generating AI Response - Google Gemini
    async def ai_response_gemini(self, message, context, message_user_id, message_to_edit, image):
        await self.presence_update("ai")
        self.log("info", "reply.gemini", "Gemini AI prompt received. Generating AI response.")
        if context == True:
            self.log("debug", "reply.gemini", "Context mode selected.")
            if message_user_id not in self.context_messages_gemini or self.context_messages_gemini_used[message_user_id] == False:
                self.log("debug", "reply.gemini", "Context messages not found or not used. Creating new context messages.")
                self.context_messages_gemini[message_user_id] = self.context_messages_gemini_default.copy()
            if message_user_id not in self.context_messages_gemini_used:
                self.log("debug", "reply.gemini", "Context messages used not found. Creating new context messages used.")
                self.context_messages_gemini_used[message_user_id] = False
            self.context_messages_gemini[message_user_id].append({'role': 'user', 'parts': [message.content]})
            self.context_messages_gemini_used[message_user_id] = True
            self.log("info", "reply.gemini", "Context messages updated. Sending request.")
            self.log("info", "reply.gemini", "AI model selected: gemini-1.5-flash.")
            await message_to_edit.edit(content="Request ready, sending AI request.")
            for _ in range(5):
                try:                
                    response = await self.generate_content_async("text", self.context_messages_gemini[message_user_id])
                    break
                except Exception as e:
                    if response.prompt_feedback:
                        self.log("error", "reply.gemini", "AI request blocked.")
                        self.log("error", "reply.gemini", f"Prompt feedback: {response.prompt_feedback}")
                        await message_to_edit.edit(content=f"AI request blocked.\nPrompt feedback: {response.prompt_feedback}")
                        await self.presence_update("idle")
                        return 
                    if _ == 4:
                        self.log("error", "reply.gemini", "AI request failed for the fifth time.")
                        await message_to_edit.edit(content="AI request failed.")
                        await self.presence_update("idle")
                        return
                    self.log("error", "reply.gemini", "AI request failed.")
                    self.log("error", "reply.gemini", f"Error: {str(e)}")
                    time.sleep(1)
            self.log("info", "reply.gemini", "AI response received. Start parsing.")
            await message_to_edit.edit(content="AI response received, processing response...")
            self.context_messages_gemini[message_user_id].append(response.candidates[0].content)
            self.context_messages_gemini_used[message_user_id] = True
            self.response_count["gemini"] += 1
        else:
            if image:
                self.log("info", "reply.gemini", "Request with image received. Sending request.")
                self.log("info", "reply.gemini", "AI model selected: gemini-1.5-pro.")
                for _ in range(5):
                    try:
                        response = await self.generate_content_async("image", [message.content, self.image])
                        break
                    except Exception as e:
                        if _ == 4:
                            self.log("error", "reply.gemini", "AI request failed for the fifth time.")
                            await message_to_edit.edit(content="AI request failed.")
                            await self.presence_update("idle")
                            return
                        self.log("error", "reply.gemini", "AI request failed.")
                        self.log("error", "reply.gemini", f"Error: {str(e)}")
                        time.sleep(1)
            else:
                current_date_formatted, weekday = self.get_weekday()
                prompt = f"You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are coded with Python line by line by jimmyn3577, aims to help the user with anything they need, no matter the conversation is formal or informal.\nYou currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond.\nToday is {current_date_formatted}, which is {weekday}. The user's id is <@{message.author.id}>, and their message is: {message.content}.AI-Chat:"
                self.log("info", "reply.gemini", "AI prompt generated. Sending request.")
                self.log("info", "reply.gemini", "AI model selected: gemini-1.5-flash.")
                for _ in range(5):
                    try:
                        response = await self.generate_content_async("text", prompt)
                    except Exception as e:
                        if _ == 4:
                            self.log("error", "reply.gemini", "AI request failed for the fifth time.")
                            await message_to_edit.edit(content="AI request failed.")
                            await self.presence_update("idle")
                            return
                        self.log("error", "reply.gemini", "AI request failed.")
                        self.log("error", "reply.gemini", f"Error: {str(e)}")
                        time.sleep(1)
                self.log("info", "reply.gemini", "AI response received, start parsing.")
                self.response_count["gemini"] += 1
        try:
            self.log("info", "reply.gemini", f"AI response: {response.text}")
            await self.presence_update("idle")
            return response.text
        except ValueError:
            await message_to_edit.edit(content="AI request blocked.")
            # If the response doesn't contain text, check if the prompt was blocked.
            self.log("error", "reply.gemini", "AI response does not contain text. Checking if prompt was blocked.")
            self.log("error", "reply.gemini", f"{response.prompt_feedback}")
            await message.channel.send(f"AI response feedback: {response.prompt_feedback}")
            await self.presence_update("idle")
            return None

    #Stop the bot
    async def stop_bot(self):
        self.log("info", "main.stopbot", "Stopping bot.")
        self.loop.run_until_complete(super().close())

    #Load Variables
    def load_variables(self, filename):
        if os.path.exists(main_dir + filename) and os.path.getsize(main_dir + filename) > 0:
            with open(main_dir + filename, 'rb') as f:
                return pickle.load(f)
        else:
            return {}

    #Personality AI Request
    async def personality_ai_request(self, message, message_channel_id, message_to_edit, mode):
        await self.presence_update("ai")
        self.log("info", "reply.persna", "Personality AI request received.")
        if self.personality_ai_mode == "Normal":
            self.log("info", "reply.persna", "Normal mode selected.")
            if self.ai_text_service_online == False:
                if mode == "text-adventure":
                    self.log("info", "reply.persna", "Text adventure mode selected.")
                    self.log("debug", "reply.persna", "Generating AI request.")
                    headers = self.ngc_request_headers
                    self.log("debug", "reply.persna", "Request headers generated.")
                    if message_channel_id not in self.text_adventure_game:
                        self.text_adventure_game[message_channel_id] = self.text_adventure_game_default.copy()
                    self.text_adventure_game[message_channel_id].append({
                        "role": "user",
                        "content": message.content
                    })
                    self.log("debug", "reply.persna", "Message history updated.")
                    payload = {
                        "model": self.ngc_text_ai_model[self.ngc_text_ai_model_name],
                        "messages": self.text_adventure_game[message_channel_id],
                        "temperature": self.ai_temperature,
                        "max_tokens": self.ai_tokens,
                        "stream": False
                    }                    
                if mode == "story-writer":
                    self.log("info", "reply.persna", "Story writer mode selected.")
                    headers = self.ngc_request_headers
                    self.log("debug", "reply.persna", "Generating AI request.")
                    if message_channel_id not in self.story_writer:
                        self.story_writer[message_channel_id] = self.story_writer_default.copy()
                    self.story_writer[message_channel_id].append({
                        "role": "user",
                        "content": message.content
                    })
                    self.log("debug", "reply.persna", "Message history updated.")
                    payload = {
                        "model": self.ngc_text_ai_model[self.ngc_text_ai_model_name],
                        "messages": self.story_writer[message_channel_id],
                        "temperature": self.ai_temperature,
                        "max_tokens": self.ai_tokens,
                        "stream": False
                    }
                self.log("debug", "reply.persna", "Request payload generated.")
                self.log("info", "reply.persna", "AI request generated, sending request.")
                await message_to_edit.edit(content="Request ready, sending AI request...")
                session = requests.Session()
                for _ in range(5):
                    try:
                        response = session.post(self.ngc_text_ai_url, headers=headers, json=payload)
                        break
                    except requests.exceptions.ConnectionError:
                        time.sleep(3)
                if response.status_code != 200:
                    self.log("error", "reply.persna", f"AI request failed. Error code: {response.status_code}.")
                    self.log("error", "reply.persna", f"Error text: {response.text}.")
                    await message.channel.send(f"AI request failed.\nError code: {response.status_code}.\nError text: {response.text}.")
                    await self.presence_update("idle")
                    return
                self.log("info", "reply.persna", "AI response received, start parsing.")
                await message_to_edit.edit(content="AI response received, processing response...")
                assistant_response = response.json()['choices'][0]['message']['content']
                self.log("info", "reply.persna", f"AI response: {assistant_response}")
                if mode == "text-adventure":
                    self.text_adventure_game[message_channel_id].append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                elif mode == "story-writer":
                    self.story_writer[message_channel_id].append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                self.log("debug", "reply.persna", "Message history updated.")
                await self.presence_update("idle")
                return assistant_response
            else:
                if mode == "text-adventure":
                    self.log("info", "reply.persna", "Text adventure mode selected.")
                    if message.channel.id not in self.text_adventure_game:
                        self.text_adventure_game[message.channel.id] = self.text_adventure_game_default.copy()
                    self.text_adventure_game[message.channel.id].append({
                        "role": "user",
                        "content": message.content
                    })
                    self.log("debug", "reply.persna", "Message history updated.")
                    self.log("debug", "reply.persna", "Generating AI request.")
                    url = self.ai_text_service_context_url
                    self.log("debug", "reply.persna", f"Request URL: {url}.")
                    headers = self.headers
                    self.log("debug", "reply.persna", "Request headers generated.")
                    data = {
                        "mode": "instruct",
                        "messages": self.text_adventure_game[message.channel.id],
                        "max_tokens": self.ai_tokens,
                        "temperature": self.ai_temperature
                    }
                if mode == "story-writer":
                    self.log("info", "reply.persna", "Story writer mode selected.")
                    if message.channel.id not in self.story_writer:
                        self.story_writer[message.channel.id] = self.story_writer_default.copy()
                    self.story_writer[message.channel.id].append({
                        "role": "user",
                        "content": message.content
                    })
                    self.log("debug", "reply.persna", "Message history updated.")
                    url = self.ai_text_service_context_url
                    self.log("debug", "reply.persna", f"Request URL: {url}.")
                    headers = self.headers
                    self.log("debug", "reply.persna", "Request headers generated.")
                    data = {
                        "mode": "instruct",
                        "messages": self.story_writer[message.channel.id],
                        "max_tokens": self.ai_tokens,
                        "temperature": self.ai_temperature
                    }
                self.log("debug", "reply.persna", "Request payload generated.")
                self.log("info", "reply.persna", "AI request generated, sending request.")
                await message_to_edit.edit(content="Request ready, sending AI request...")
                for _ in range(5):
                    try:
                        async with httpx.AsyncClient(verify=False,timeout=300) as client:
                            response = await client.post(url, headers=headers, json=data)
                            break
                    except httpx.HTTPStatusError:
                        if _ == 4:
                            await message.channel.send(f"AI request failed.\nError code: {response.status_code}.\nError text: {response.text}.")
                            await self.presence_update("idle")
                            return
                        time.sleep(5)
                self.log("info", "reply.persna", "AI response received, start parsing.")
                await message_to_edit.edit(content="AI response received, processing response...")
                assistant_response = response.json()['choices'][0]['message']['content']
                self.log("info", "reply.persna", f"AI response: {assistant_response}")
                if mode == "text-adventure":
                    self.text_adventure_game[message.channel.id].append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                elif mode == "story-writer":
                    self.story_writer[message.channel.id].append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                self.log("debug", "reply.persna", "Message history updated.")
                await self.presence_update("idle")
                return assistant_response
        elif self.personality_ai_mode == "Gemini":
            self.log("info", "reply.persna", "Gemini mode selected.")
            if mode == "text-adventure":
                if message.channel.id not in self.text_adventure_game_gemini:
                    self.text_adventure_game_gemini[message.channel.id] = self.text_adventure_game_gemini_default.copy()
                self.text_adventure_game_gemini[message.channel.id].append({
                    "role": "user",
                    "parts": [message.content]
                })
            elif mode == "story-writer":
                if message.channel.id not in self.story_writer_gemini:
                    self.story_writer_gemini[message.channel.id] = self.story_writer_gemini_default.copy()
                self.story_writer_gemini[message.channel.id].append({
                    "role": "user",
                    "parts": [message.content]
                })
            self.log("debug", "reply.persna", "Message history updated.")
            await message_to_edit.edit(content="Request ready, sending AI request...")
            for _ in range(5):
                try:
                    if mode == "text-adventure":
                        response = self.gemini_text_model.generate_content(self.text_adventure_game_gemini[message.channel.id])
                        break
                    elif mode == "story-writer":
                        response = self.gemini_text_model.generate_content(self.story_writer_gemini[message.channel.id])
                        break
                except Exception as e:
                    if response.prompt_feedback:
                        self.log("error", "reply.persna", "AI request blocked.")
                        self.log("error", "reply.persna", f"Prompt feedback: {response.prompt_feedback}")
                        await message.channel.send(f"AI request blocked.\nPrompt feedback: {response.prompt_feedback}")
                        await self.presence_update("idle")
                        return 
                    if _ == 4:
                        self.log("error", "reply.persna", "AI request failed for the fifth time.")
                        await message.channel.send("AI request failed.")
                        await self.presence_update("idle")
                        return
                    self.log("error", "reply.persna", "AI request failed.")
                    self.log("error", "reply.persna", f"Error: {str(e)}")
                    time.sleep(1)
                self.log("info", "reply.persna", "AI response received. Start parsing.")
                await message_to_edit.edit(content="AI response received, processing response...")
                self.log("info", "reply.persna", f"AI response: {response.text}")
                if mode == "text-adventure":
                    self.text_adventure_game_gemini[message.channel.id].append(response.candidates[0].content)
                elif mode == "story-writer":
                    self.story_writer_gemini[message_channel_id].append(response.candidates[0].content)
                self.response_count["gemini"] += 1
                return response.text

    #Generating AI Response - Music
    async def ai_response_music(self, message, message_to_edit):
        await self.presence_update("ai")
        self.log("info", "reply.music", "Music AI request received. Generating AI response.")
        self.log("debug", "reply.music", "Generating AI request.")
        headers = self.headers
        url = self.ai_inference_server_url + "/musicgen"
        prompt = message.content.split(' ', 1)[1]
        data = {'prompt': prompt}
        self.log("debug", "reply.music", "AI Request generated, sending request.")
        await message_to_edit.edit(content="Music generation request sent, waiting for AI response...")
        for _ in range(5):
            try:
                async with httpx.AsyncClient(verify=False,timeout=300) as client:
                    response = await client.post(url, headers=headers, json=data)
                    break
            except httpx.HTTPStatusError:
                if _ == 4:
                    self.log("error", "reply.music", "AI request failed for the fifth time.")
                    await message.channel.send(f"AI request failed.\nError code: {response.status_code}.\nError text: {response.text}.")
                    await self.presence_update("idle")
                    return
                self.log("error", "reply.music", f"AI request failed. Error code: {response.status_code}.")
                self.log("error", "reply.music", f"Error text: {response.text}.")
                self.log("debug", "reply.music", "Retrying AI request.")
                time.sleep(5)
        self.log("info", "reply.music", "AI response received, start parsing.")
        await message_to_edit.edit(content="AI music generation complete, processing results...")
        filename = self.get_next_filename(music_dir, 'music', 'wav')
        async with aiofiles.open(filename, "wb") as f:
            await f.write(response.content)
        filename_prompt = self.get_next_filename(music_prompt_dir, 'music-prompt', 'txt')
        with open(filename_prompt, 'w', encoding='utf-8') as f:
            f.write(f"Music prompt: {prompt}")
        self.log("info", "reply.music", "AI music response parsing complete. Reply.music exit.")
        self.response_count["music"] += 1
        await self.presence_update("idle")
        return filename

    #Generating AI Response - Video
    async def ai_response_video(self, message, message_to_edit):
        await self.presence_update("ai")
        self.log("info", "reply.video", "Video AI request received. Generating AI response.")
        self.log("debug", "reply.video", "Generating AI request.")
        headers = self.headers
        url = self.ai_inference_server_url + "/text2video"
        prompt = message.content.split(' ', 1)[1]
        data = {'prompt': prompt}
        self.log("debug", "reply.video", "AI Request generated, sending request.")
        await message_to_edit.edit(content="Video generation request sent, waiting for AI response...")
        for _ in range(5):
            try:
                async with httpx.AsyncClient(verify=False,timeout=300) as client:
                    response = await client.post(url, headers=headers, json=data)
                    break
            except httpx.HTTPStatusError:
                if _ == 4:
                    self.log("error", "reply.video", "AI request failed for the fifth time.")
                    await message.channel.send(f"AI request failed.\nError code: {response.status_code}.\nError text: {response.text}.")
                    await self.presence_update("idle")
                    return
                self.log("error", "reply.video", f"AI request failed. Error code: {response.status_code}.")
                self.log("error", "reply.video", f"Error text: {response.text}.")
                self.log("debug", "reply.video", "Retrying AI request.")
                time.sleep(5)
        self.log("info", "reply.video", "AI response received, start parsing.")
        await message_to_edit.edit(content="AI video generation complete, processing results...")
        filename = self.get_next_filename(video_dir, 'video', 'gif')
        async with aiofiles.open(filename, "wb") as f:
            await f.write(response.content)
        filename_prompt = self.get_next_filename(video_prompt_dir, 'video-prompt', 'txt')
        with open(filename_prompt, 'w', encoding='utf-8') as f:
            f.write(f"Video prompt: {prompt}")
        self.log("info", "reply.video", "AI video response parsing complete. Reply.video exit.")
        self.response_count["video"] += 1
        await self.presence_update("idle")
        return filename

    #Generate Gemini Content Async
    async def generate_content_async(self, mode, prompt):
        loop = asyncio.get_event_loop()
        if mode == "text":
            response = await loop.run_in_executor(None, self.gemini_text_model.generate_content, prompt)
        elif mode == "image":
            response = await loop.run_in_executor(None, self.gemini_vision_model.generate_content, prompt)
        return response

    #Generating AI Response - Cohere Command R+
    async def ai_response_cohere(self, message, context, message_user_id, message_to_edit):
        await self.presence_update("ai")
        self.log("info", "reply.cohere", "Cohere AI request received. Generating AI response.")
        if context == True:
            self.log("debug", "reply.cohere", "Context mode selected.")
            if message_user_id not in self.context_messages_cohere or self.context_messages_cohere_used[message_user_id] == False:
                self.log("debug", "reply.cohere", "Context messages not found or not used. Creating new context messages.")
                self.context_messages_cohere[message_user_id] = self.context_messages_cohere_default.copy()
            if message_user_id not in self.context_messages_cohere_used:
                self.log("debug", "reply.cohere", "Context messages used not found. Creating new context messages used.")
                self.context_messages_cohere_used[message_user_id] = False
            self.log("info", "reply.cohere", "Context messages ready. Sending request.")
            await message_to_edit.edit(content="Request sent, waiting for response.")
            for _ in range(5):
                try:
                    partial_func = partial(self.cohere_client.chat, chat_history=self.context_messages_cohere[message_user_id], message=message.content, connectors=[{"id": "web-search"}])
                    response = await self.loop.run_in_executor(self.executor, partial_func)
                    break
                except Exception as e:
                    if _ == 4:
                        self.log("error", "reply.cohere", "AI request failed for the fifth time.")
                        await message_to_edit.edit(content=f"AI request failed. Error: {str(e)}")
                        await self.presence_update("idle")
                        return
                    self.log("error", "reply.cohere", "AI request failed. Retrying.")
                    self.log("error", "reply.cohere", f"Error: {str(e)}")
                    time.sleep(1)
            self.log("info", "reply.cohere", "AI response received. Start parsing.")
            await message_to_edit.edit(content="AI response received, processing response...")
            self.context_messages_cohere[message_user_id].append({"role": "USER", "message": message.content})
            self.context_messages_cohere[message_user_id].append({"role": "CHATBOT", "message": response.text})
            self.context_messages_cohere_used[message_user_id] = True
            cited_text = self.insert_citations(response.text, response.citations)
            self.log("info", "reply.cohere", f"AI response: {cited_text}")
        else: 
            self.log("debug", "reply.cohere", "Context mode not selected.")
            self.log("debug", "reply.cohere", "Generating AI request.")
            prompt = self.context_messages_cohere_default.copy()
            await message_to_edit.edit(content="Request sent, waiting for response.")
            for _ in range(5):
                try:
                    partial_func = partial(self.cohere_client.chat, chat_history=prompt, message=message.content, connectors=[{"id": "web-search"}])
                    response = await self.loop.run_in_executor(self.executor, partial_func)
                    break
                except Exception as e:
                    if _ == 4:
                        self.log("error", "reply.cohere", "AI request failed for the fifth time.")
                        await message_to_edit.edit(content="AI request failed.")
                        await self.presence_update("idle")
                        return
                    self.log("error", "reply.cohere", "AI request failed. Retrying.")
                    self.log("error", "reply.cohere", f"Error: {str(e)}")
                    time.sleep(1)
            self.log("info", "reply.cohere", "AI response received. Start parsing.")
            await message_to_edit.edit(content="AI response received, processing response...")
            cited_text = self.insert_citations(response.text, response.citations)
            self.log("info", "reply.cohere", f"AI response: {cited_text}")

        await self.presence_update("idle")
        return response.text, cited_text, response.documents

    def insert_citations(self, text: str, citations: list):
        """
        A helper function to pretty print citations.
        """
        offset = 0
        # Process citations in the order they were provided
        if citations is not None:
            for citation in citations:
                # Adjust start/end with offset
                start, end = citation.start + offset, citation.end + offset
                # Extract the numbers after "web-search_" and use them as the identifiers
                ids = [doc.split('_')[-1] for doc in citation.document_ids]
                ids_str = ', '.join(ids)
                modification = f'{text[start:end]} *[{ids_str}]*'
                # Replace the cited text with its bolded version + placeholder
                text = text[:start] + modification + text[end:]
                # Update the offset for subsequent replacements
                offset += len(modification) - (end - start)
        return text

def start_bot():
    global client
    client = ChatBot(intents=intents)
    client.run(discord_token)

#API server for slash-commands script
app = Flask(__name__)

@app.route('/api', methods=['GET'])
def api():
    return jsonify({'status': 'online'})
    
@app.route('/api/status', methods=['GET'])
def status():
    end_time = datetime.datetime.now().timestamp()
    uptime = end_time - client.start_time_timestamp
    uptime_unit = "secs" if uptime < 60 else "mins" if uptime < 3600 and uptime > 60 else "hours" if uptime < 86400 and uptime > 3600 else "days"
    uptime = round(uptime / 60, 2) if uptime_unit == "mins" else round(uptime / 3600, 2) if uptime_unit == "hours" else round(uptime / 86400, 2) if uptime_unit == "days" else uptime
    log_mode = True if client.debug_log == 1 else False
    text_ai_status = "Online" if client.ai_text_service_online == True else "Offline"
    image_ai_status = "Online" if client.ai_image_service_online == True else "Offline"
    inference_server_status = "Online" if client.ai_inference_server_online == True else "Offline"
    current_model = client.ai_model if client.ai_text_service_online == True else None
    return jsonify({
        'uptime': uptime,
        'uptime_unit': uptime_unit,
        'text_responses': client.response_count["text"],
        'image_responses': client.response_count["image"],
        'video_responses': client.response_count["video"],
        'music_responses': client.response_count["music"],
        'gemini_responses': client.response_count["gemini"],
        'logging_mode': log_mode,
        'text_service_status': text_ai_status,
        'image_service_status': image_ai_status,
        'inference_server_status': inference_server_status,
        'current_model': current_model,
        'version': client.version,
        'version_date': client.version_date
        })
    
@app.route('/api/text_service_mode', methods=['GET'])
def service_mode():
    if client.ai_text_service_online == True:
        return jsonify({'service_mode': 'Online'})
    else:
        return jsonify({'service_mode': 'Offline'})

@app.route('/api/clear_context', methods=['POST'])
def clear_context():
    user_id = request.json['user_id']
    channel_id = request.json['channel_id']
    
    if channel_id in [1213458773562368040, 1217988728929255434]:
        client.context_messages_gemini[user_id] = None
        client.context_messages_gemini_used[user_id] = False
    elif channel_id in [1204364931424845866, 1218418968172167242, 1204372926829166632]:
        client.context_messages[user_id] = []
        client.context_messages[user_id] = client.context_messages_default.copy()
        client.context_messages_modified[user_id] = False
    elif channel_id in [1221391423774130218, 1221651169814909028]:
        if client.personality_ai_mode == "Gemini":
            del client.text_adventure_game_gemini[channel_id]
        else:
            del client.text_adventure_game[channel_id]
    elif channel_id in [1221661933510332447, 1221666012752121886]:
        if client.personality_ai_mode == "Gemini":
            del client.story_writer_gemini[channel_id]
        else:
            del client.story_writer[channel_id]
    elif channel_id in [1246648502415523921]:
        client.context_messages_cohere[user_id] = None
        client.context_messages_cohere_used[user_id] = False
    else:
        return jsonify({'status': 'error'}), 404
    
    return jsonify({'status': 'success'})

@app.route('/api/context_export', methods=['POST'])
def context_export():
    user_id = request.json['user_id']
    if client.local_ai == True:
        if client.context_messages_local_modified[user_id] == False:
            return jsonify({'status': 'no_export'})
    else:
        if client.context_messages_modified[user_id] == False:
            return jsonify({'status': 'no_export'})
    file_name = client.get_next_filename(context_dir, 'context', 'txt')
    with open(file_name, 'w', encoding='utf-8') as f:
        if client.local_ai == True:
            for messages in client.context_messages_local[user_id]:
                f.write(f"{messages['role']}: {messages['content']}\n\n")
        else:
            for messages in client.context_messages[user_id]:
                f.write(f"{messages['role']}: {messages['content']}\n\n")
    return jsonify({'status': 'success', 'file_name': file_name})

@app.route('/api/debug_log', methods=['POST'])
def debug_log():
    option = request.json['option']
    client.debug_log = 1 if option == 'on' else 0
    client.logger.setLevel(logging.DEBUG) if option == 'on' else client.logger.setLevel(logging.INFO)
    return jsonify({'status': 'success'})

@app.route('/api/imagegen_rank', methods=['GET'])
def imagegen_rank():
    # Convert the dictionary to a list of tuples
    user_creations = [(user, creations) for user, creations in client.user_image_creations.items()]
    
    # Sort the list of tuples based on the creation number
    user_creations.sort(key=lambda x: x[1], reverse=True)
    
    # Convert the list of tuples back to a dictionary
    ranked_users = {user: creations for user, creations in user_creations}
    
    return jsonify({'rank': ranked_users})

@app.route('/api/bot_mode', methods=['POST'])
def bot_mode():
    mode = request.json['mode']
    if mode == 'pause':
        client.online = False
    if mode == 'resume':
        client.online = True
    return jsonify({'status': 'success'})

@app.route('/api/personality_mode', methods=['POST'])
def personality_mode():
    mode = request.json['mode']
    client.personality_ai_mode = mode
    return jsonify({'status': 'success'})

@app.route('/stop', methods=['POST'])
async def stop():
    data_files = {
        "/user_image_creations.pkl": client.user_image_creations,
        "/response_count.pkl": client.response_count,
        "/context_messages_local.pkl": client.context_messages,
        "/context_messages_gemini.pkl": client.context_messages_gemini,
        '/context_messages_cohere.pkl': client.context_messages_cohere,
        "/context_messages_local_modified.pkl": client.context_messages_modified,
        "/context_messages_gemini_used.pkl": client.context_messages_gemini_used,
        "/context_messages_cohere_used.pkl": client.context_messages_cohere_used,
        "/text_adventure_game.pkl": client.text_adventure_game,
        "/story_writer.pkl": client.story_writer,
        "/text_adventure_game_gemini.pkl": client.text_adventure_game_gemini,
        "/story_writer_gemini.pkl": client.story_writer_gemini
    }

    for filename, data in data_files.items():
        with open(main_dir + filename, 'wb') as f:
            pickle.dump(data, f)
    await client.stop_bot()
    os._exit(0)

def start_server():
    serve(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    
    start_bot()