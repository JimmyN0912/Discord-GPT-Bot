import discord
import requests
import json
import nest_asyncio
import datetime
import logging
import Levenshtein
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

nest_asyncio.apply()
load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

#Check if main directory exists, if not, create it
main_dir = 'C:\GPT-Bot'
if not os.path.exists(main_dir):
    os.makedirs(main_dir)

#Check if log directory exists, if not, create it
log_dir = main_dir + '\logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

#Check if context directory exists, if not, create it
context_dir = main_dir + '\context'
if not os.path.exists(context_dir):
    os.makedirs(context_dir)

#Check if image directory exists, if not, create it
image_dir = main_dir + '\images'
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

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
    # model.loader

class ChatBot(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)

        #Logger Setup
        self.logger = logger

        #Variables
        self.response_count_local = 0
        self.response_count_ngc = 0
        self.response_count_image_ngc = 0
        self.start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.start_time_timestamp = datetime.datetime.now().timestamp()
        self.weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        #Settings
        self.local_ai = None
        self.debug_log = 1
        self.local_ai_headers= {"Content-Type": "application/json"}
        self.local_ai_url= "http://192.168.0.175:5000/v1/completions"
        self.local_ai_context_url = "http://192.168.0.175:5000/v1/chat/completions"
        self.local_ai_model = None
        self.request_successful = None
        self.ngc_api_token = os.getenv('NGC_API_TOKEN')
        self.ngc_request_headers = {
            "Authorization": self.ngc_api_token,
            "Accept": "application/json",
        }
        self.ngc_request_headers_context = {
            "Authorization": self.ngc_api_token,
            "accept": "text/event-stream",
            "content-type": "application/json"
        }
        self.ngc_ai_invoke_url = {"llama-2-70b": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/0e349b44-440a-44e1-93e9-abe8dcb27158",
                                  "yi-34b": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/347fa3f3-d675-432c-b844-669ef8ee53df",
                                  "mixtral-8x7b-instruct": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/8f4118ba-60a8-4e6b-8574-e38a4067a4a3",
                                  "code-llama-70b": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/2ae529dc-f728-4a46-9b8d-2697213666d8",
                                  "Gemma-7b": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/1361fa56-61d7-4a12-af32-69a3825746fa",
                                  "Mamba-Chat": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/381be320-4721-4664-bd75-58f8783b43c7",
                                  "SDXL": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/89848fb8-549f-41bb-88cb-95d6597044a4"}
        self.ngc_ai_model = "mixtral-8x7b-instruct"
        self.ngc_ai_fetch_url_format = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/"
        self.ai_tokens = 512
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
            }
        })
        self.context_messages_default = [
            {
                "role": "user",
                "content": "You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are coded with Python line by line by jimmyn3577, aims to help the user with anything they need, no matter the conversation is formal or informal.\nYou currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond."
            }
        ]
        self.context_messages = {}
        self.context_messages_local = {}
        self.context_messages_modified = {}
        self.context_messages_local_modified = {}

        #Startup messages
        self.log("info", "main.startup", "Discord Bot V11.10 (2024.2.23).")
        self.log("info", "main.startup", "Discord Bot system starting...")
        self.log("info", "main.startup", f"start_time_timestamp generated: {self.start_time_timestamp}.")
        self.log("debug", "main.startup", f"start_time generated: {self.start_time}.")
        self.log("info", "main.startup", "System startup complete.")
        self.log("info", "main.startup", "Startup thread exit.")

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
        elif service == "reply.llmsvc" or service == "reply.llmctx":
            color = colorama.Fore.LIGHTMAGENTA_EX
        elif service == "reply.ngcsvc" or service == "reply.ngcctx" or service == "reply.ngcimg":
            color = colorama.Fore.GREEN
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
        self.log("info", "main.startup", "Connection thread exit.")
        await self.presence_update("idle")
        #Testing AI system status
        service_check_task = asyncio.create_task(self.auto_service_check())
    
    # Receiving messages
    async def on_message(self, message):
        #Actions if message comes from bot
        if message.author == self.user:
            self.log("debug", "message.recv", "Message received. Author is Bot, ignoring message.")
            return

        #Announcing message
        self.log("info", "message.recv", f"Message Received: '{message.content}', from {message.author.name}, in {message.guild.name} / {message.channel.category.name} / {message.channel}.")
        self.log("debug", "message.recv", f"Message ID: {message.id}. Message Replying: {message.reference}. ")
            
        #Actions if bot isn't mentioned in message
        if f'<@1086616278002831402>' not in message.content:
            self.log("info", "message.recv", "Bot not mentioned in message, ignoring message.")
            return
        
        if message.channel.category.name == 'Chatting-聊天區':
            self.log("info", "message.proc", "Message is in Chatting-聊天區, rejecting message.")
            await message.channel.send("Please use other channels for chatting with the bot.\n請使用其他頻道與機器人聊天。")
            return
        

        #Generating AI Response

        if message.channel.category.name == 'text-to-image':
            init_message = await message.channel.send("Generating image...")
            image = await self.ai_response_image(message)
            await init_message.delete()
            await message.channel.send(file=discord.File(image))
            # send image
            self.log("info", "reply.ngcimg", "Image sent.")
            return
        
        message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")
        message_user_id = message.author.id
        if message_user_id not in self.context_messages:
            self.context_messages[message_user_id] = self.context_messages_default.copy()
            self.context_messages_modified[message_user_id] = False
        if message_user_id not in self.context_messages_local:
            self.context_messages_local[message_user_id] = self.context_messages_default.copy()
            self.context_messages_local_modified[message_user_id] = False

        if self.local_ai == True:
            if message.channel.name == 'stream':
                await self.ai_response_streaming(message,message_to_edit)
                return
                          
            else:
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
            if message.channel.name == 'stream':
                await self.ngc_ai_response_streaming(message,message_to_edit)
                return
            
            else:
                context = True if message.channel.name == 'context' else False
                if context == True:
                    self.log("info", "message.proc", "Starting reply.ngcctx process.")
                else:
                    self.log("info", "message.proc", "Starting reply.ngcsvc process.")
                assistant_response = await self.ngc_ai_request(message, message_to_edit, context, message_user_id)
                self.log("info", "message.send", "Sending message.")
                await message_to_edit.edit(content=f"*Model Used: {self.ngc_ai_model}*")
                self.log("info", "message.send", f"Message sent. AI model used: {self.ngc_ai_model}.")
                await self.send_message(message,assistant_response)

    #Generating AI Response - Local Mode
    async def ai_request(self, message, message_to_edit, context, message_user_id):
        await self.presence_update("ai")

        ### Generating AI Request ###
        service = "reply.llmsvc" if context == False else "reply.llmctx"
        self.log("info", service, "Generating AI request.")
        #Set max tokens
        max_tokens = self.ai_tokens
        self.log("debug", service, f"AI max tokens: {max_tokens}.")
        #Generate request headers
        headers = self.local_ai_headers
        self.log("debug", service, f"AI request headers generated: {headers}.")
        if context == True:
            #Set request URL
            url = self.local_ai_context_url
            self.log("debug", service, f"AI request URL: {url}.")
            if self.context_messages_local_modified[message_user_id] == False:
                current_date_formatted, weekday = self.get_weekday()
                prompt = f"Today is {current_date_formatted}, which is {weekday}. The user's id is <@{message.author.id}>, and their message is: {message.content}."
                self.context_messages_local[message_user_id].append({
                    "role": "user",
                    "content": prompt
                })
                self.context_messages_local_modified = True
            else:
                self.context_messages_local[message_user_id].append({
                    "role": "user",
                    "content": message.content
                })
            self.log("debug", service, "Message history updated.")
            #Combine request data
            data = {
                "mode": "instruct",
                "messages": self.context_messages_local[message_user_id],
                "max_tokens": self.ai_tokens,
                "temperature": self.ai_temperature
            }
        else:
            #Set request URL
            url = self.local_ai_url
            self.log("debug", service, f"AI request URL: {url}.")
            current_date_formatted, weekday = self.get_weekday()
            #Generating AI Prompt
            ai_prompt = f"You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are coded with Python line by line by jimmyn3577, aims to help the user with anything they need, no matter the conversation is formal or informal.\nYou currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond.\nToday is {current_date_formatted}, which is {weekday}. The user's id is <@{message.author.id}>, and their message is: {message.content}.AI-Chat:"
            self.log("debug", service, f"AI Prompt generated.")
            #Combine request data
            data = {
            "prompt": ai_prompt,
            "max_tokens": max_tokens,
            "temperature": self.ai_temperature
            }
        self.log("debug", service, f"AI request data generated.")
        self.log("info", service, "AI request generated, sending request.")
        update_task = asyncio.create_task(self.update_time(message_to_edit))
        try:
            async with httpx.AsyncClient(verify=False,timeout=300) as client:
                response = await client.post(url, headers=headers, json=data)
                self.request_successful = True
        except (httpx.ConnectError, httpx.ReadError):
            self.log("error", service, "AI request failed, connection error. The AI service may be down.")
            await message.channel.send("AI request failed, connection error. The AI service may be down. Please use '!service check' to check the AI service status, and try again.")
            update_task.cancel()
            self.request_successful = False
            await self.presence_update("idle")
            self.log("info", service, "reply.llmsvc process exit.")
            return
        self.log("info", service, "AI response received, start parsing.")
        update_task.cancel()
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
        assistant_response = response.json()['choices'][0]['text'] if context == False else response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        if context == True:
            self.context_messages_local[message_user_id].append({
                "role": "assistant",
                "content": assistant_response
            })
            self.log("debug", "reply.parser", "Message history updated.")
        #Extracting AI model used
        model_used = response.json()['model']
        self.log("debug", "reply.parser", f"AI model used: {model_used}")
        #Extracting AI prompt tokens
        prompt_tokens = response.json()['usage']['prompt_tokens']
        self.log("debug", "reply.parser", f"AI prompt tokens: {prompt_tokens}")
        #Extracting AI predict tokens
        completion_tokens = response.json()['usage']['completion_tokens']
        self.log("debug", "reply.parser", f"AI predict tokens: {completion_tokens}")
        self.response_count_local += 1
        self.log("debug", "reply.parser", f"Responses since start (Local): {self.response_count_local}")
        await self.presence_update("idle")
        self.log("info", "reply.parser", "AI response parsing complete. Reply.parse exit.")

        return assistant_response, model_used
        
    #Streaming AI Response - Local Mode
    async def ai_response_streaming(self, message, message_to_edit):
        await self.presence_update("ai")
        self.log("info", "reply.llmsvc", "Generating AI request.")
        # Set request URL
        url = self.local_ai_url
        self.log("debug", "reply.llmsvc", f"AI request URL: {url}.")
        # Generate request headers
        headers = self.local_ai_headers
        self.log("debug", "reply.llmsvc", f"AI request headers generated: {headers}.")
        prompt = f"You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are designed to help the user with anything they need, no matter the conversation is formal or informal.\n You currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond.\nThe user's id is <@{message.author.id}>, and their message is: {message.content}.AI-Chat:"
        # Combine request data
        data = {
            "prompt": prompt,
            "max_tokens": self.ai_tokens,
            "temperature": self.ai_temperature,
            "stream": True
        }
        self.log("debug", "reply.llmsvc", f"AI request data generated.")
        self.log("info", "reply.llmsvc", "AI request generated, sending request.")
        # Send request
        timeout = httpx.Timeout(10.0, read=300.0)
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            async with client.stream("POST", url, headers=headers, json=data) as stream_response:
                self.log("info", "reply.llmsvc", "AI response received, start parsing.")
                self.log("info", "reply.llmsvc", "Starting to stream response.")
                new_content = ''
                async for line in stream_response.aiter_lines():
                    if line.startswith('data: '):  # Check if line is a data field
                        json_str = line[6:]  # Remove 'data: ' prefix
                        try:
                            payload = json.loads(json_str)
                            response_text = payload['choices'][0]['text']
                            if response_text.strip():
                                new_content += response_text
                                await message_to_edit.edit(content=new_content)
                        except json.JSONDecodeError:
                            self.log("error", "reply.llmsvc", f"Failed to decode line: {line}")
        self.response_count_local += 1
        self.log("debug", "reply.parser", f"Responses since start (Local): {self.response_count_local}")
        await self.presence_update("idle")
        self.log("info", "reply.llmsvc", "AI response streaming complete. Reply.llmsvc exit.")
    
    #Generating AI Response - NGC Mode
    async def ngc_ai_request(self,message, message_to_edit, context, message_user_id):
        await self.presence_update("ai")

        ### Generating AI Request ###
        service = "reply.ngcsvc" if context == False else "reply.ngcctx"
        self.log("info", service, "Generating AI request.")    
        #Set request URL
        invoke_url = self.ngc_ai_invoke_url[self.ngc_ai_model]
        self.log("debug", service, f"AI model: {self.ngc_ai_model}.")
        self.log("debug", service, f"Request URL: {invoke_url}.")
        #Set fetch URL
        fetch_url_format = self.ngc_ai_fetch_url_format
        self.log("debug", service, f"AI fetch URL: {fetch_url_format}.")
        #Generate request headers
        headers = self.ngc_request_headers
        self.log("debug", service, f"AI request headers generated.")
        if context == True:
            #Update message history
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
            #Generate request payload
            payload = {
                "messages": self.context_messages[message_user_id],
                "temperature": self.ai_temperature,
                "max_tokens": self.ai_tokens,
                "stream": False
            }
        else:
            current_date = datetime.datetime.now()
            current_date_formatted = current_date.strftime('%Y-%m-%d')
            weekday = self.weekday_names[current_date.weekday()]
            #Generate AI Prompt
            prompt = f"You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are coded with Python line by line by jimmyn3577, aims to help the user with anything they need, no matter the conversation is formal or informal.\n You currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond.\nToday is {current_date_formatted}, which is {weekday}. The user's id is <@{message.author.id}>, and their message is: {message.content}.AI-Chat:"
            self.log("debug", service, f"AI Prompt generated.")
            #Generate request payload
            payload = {
                "messages": [
                    {
                    "content": prompt,
                    "role": "user"
                    }
                ],
                "temperature": self.ai_temperature,
                "max_tokens": self.ai_tokens,
                "stream": False
            }
        #re-use connections
        session = requests.Session()
        self.log("info", "reply.ngcsvc", "AI request generated, sending request.")
        update_task = asyncio.create_task(self.update_time(message_to_edit))
        for _ in range(5):
            try:
                response = session.post(invoke_url, headers=headers, json=payload)
                break
            except requests.exceptions.ConnectionError:
                time.sleep(3)
        #Check if response is ready
        while response.status_code == 202:
            request_id = response.headers.get("NVCF-REQID")
            fetch_url = fetch_url_format + request_id
            response = session.get(fetch_url, headers=headers)
        self.log("info", "reply.ngcsvc", "AI response received, start reply.parser process.")
        update_task.cancel()

        ### Parsing AI Response ###
        if response.status_code != 200:
            self.log("error", "reply.parser", f"AI response status code: {response.status_code}.")
            self.log("error", "reply.parser", f"AI response text: {response.text}.")
            await self.presence_update("idle")
            self.log("info", "reply.parser", "AI response parsing complete. Reply.parse exit.")
            return
        self.log("info", "reply.parser", "Parsing AI response.")
        #Extracting AI response
        assistant_response = response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        if context == True:
            self.context_messages[message_user_id].append({
                "role": "assistant",
                "content": assistant_response
            })
            self.log("debug", "reply.parser", "Message history updated.")
        #Extracting AI prompt tokens
        prompt_tokens = response.json()['usage']['prompt_tokens']
        self.log("debug", "reply.parser", f"AI prompt tokens: {prompt_tokens}")
        #Extracting AI predict tokens
        completion_tokens = response.json()['usage']['completion_tokens']
        self.log("debug", "reply.parser", f"AI predict tokens: {completion_tokens}")
        self.response_count_ngc += 1
        self.log("debug", "reply.parser", f"Responses since start (NGC): {self.response_count_ngc}")
        await self.presence_update("idle")
        self.log("info", "reply.parser", "AI response parsing complete. Reply.parser exit.")

        return assistant_response
    
    #Get next filename (for context export)
    def get_next_filename(self, directory, base_filename, file_extension):
        i = 1
        while True:
            filename = f"{directory}/{base_filename}-{i}.{file_extension}"
            if not os.path.exists(filename):
                return filename
            i += 1

    #Streaming AI Response - NGC Mode
    async def ngc_ai_response_streaming(self,message,message_to_edit):
        await self.presence_update("ai")
        self.log("info", "reply.ngcsvc", "Generating AI request.")
        #Set request URL
        invoke_url = self.ngc_ai_invoke_url[self.ngc_ai_model]
        self.log("debug", "reply.ngcsvc", f"AI model: {self.ngc_ai_model} / Request URL: {invoke_url}.")
        headers = self.ngc_request_headers_context
        self.log("debug", "reply.ngcsvc", f"AI request headers generated:\n{headers}.")
        prompt = f"You are AI-Chat, or as the users call you, <@1086616278002831402>. You are a Discord bot in jimmyn3577's server, and you are designed to help the user with anything they need, no matter the conversation is formal or informal.\n You currently can only reply to the user's requests only with your knowledge, internet connectivity and searching may come in a future update. You currently don't have any server moderation previleges, it also may come in a future update.\nWhen responding, you are free to mention the user's id in the reply, but do not mention your id, <@1086616278002831402>, in the reply, as it will be automatically shown on top of your reply for the user to see.\n The following message is the user's message or question, please respond.\nThe user's id is <@{message.author.id}>, and their message is: {message.content}.AI-Chat:"
        self.log("debug", "reply.ngcsvc", f"AI Prompt generated.")
        payload = {
            "messages": [
                {
                "content": prompt,
                "role": "user"
                }
            ],
            "temperature": self.ai_temperature,
            "max_tokens": self.ai_tokens,
            "stream": True
        }
        self.log("debug", "reply.ngcsvc", f"AI request payload generated.")

        async with httpx.AsyncClient(verify=True) as client:
            async with client.stream('POST', invoke_url, headers=headers, json=payload) as response:
                assistant_responses = []
                partial_line = ""

                async for chunk in response.aiter_bytes():
                    text = (partial_line + chunk.decode('utf-8')).splitlines()

                    if text[-1][-6:] != '[DONE]':
                        partial_line = text[-1]
                        text = text[:-1]
                    else:
                        partial_line = ""

                    for line in text:
                        if line:  # check if line is not empty
                            try:
                                json_line = json.loads(line.replace('data: ', '', 1))  # remove 'data: ' from the line
                                assistant_responses.append(json_line['choices'][0]['delta']['content'])
                                await message_to_edit.edit(content=''.join(assistant_responses))
                            except json.decoder.JSONDecodeError:
                                if line == 'data: [DONE]':
                                    self.response_count_ngc += 1
                                    self.log("debug", "reply.parser", f"Responses since start (NGC): {self.response_count_ngc}")
                                    self.log("info", "reply.ngcsvc", "AI response finished.")
                                continue

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
            await self.change_presence(activity=discord.Game(name="the waiting game."))
            self.log("debug", "main.setprsc", "Bot presence set to 'Playing the waiting game'.")
        elif activity == 'status':
            await self.change_presence(activity=discord.Streaming(name="the status report.", url="https://www.huggingface.co/"))
            self.log("debug", "main.setprsc", "Bot presence set to 'Streaming the status report'.")
        elif activity == 'ai':
            await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
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
    async def ai_response_image(self, message):
        await self.presence_update("ai")
        self.log("info", "reply.ngcimg", "AI image prompt received. Generating AI image.")
        # Set request URL
        invoke_url = self.ngc_ai_invoke_url["SDXL"]
        self.log("debug", "reply.ngcimg", f"Request URL: {invoke_url}.")
        fetch_url_format = self.ngc_ai_fetch_url_format
        #Headers
        headers = self.ngc_request_headers
        #Generate request payload
        prompt = message.content.split(' ', 1)[1]
        self.log("debug", "reply.ngcimg", f"AI prompt: {prompt}.")
        payload = {
            "prompt": prompt,
            "sampler": "DPM",
            "guidance_scale": 5,
            "inference_steps": 25,
            "seed": 0
            }
        # re-use connections
        session = requests.Session()
        self.log("info", "reply.ngcimg", "AI request generated, sending request.")
        for _ in range(5):
            try:
                response = session.post(invoke_url, headers=headers, json=payload)
                break
            except requests.exceptions.ConnectionError:
                time.sleep(5)
        self.log("info", "reply.ngcimg", "AI response received, start parsing.")
        while response.status_code == 202:
            request_id = response.headers.get("NVCF-REQID")
            fetch_url = fetch_url_format + request_id
            response = session.get(fetch_url, headers=headers)

        response.raise_for_status()
        self.log("debug", "reply.ngcimg", "Decoding image.")
        base64_string = response.json()["b64_json"]
        # decode base64 string
        image_bytes = base64.b64decode(base64_string)
        # convert bytes to image
        image = Image.open(io.BytesIO(image_bytes))
        # save image
        filename = self.get_next_filename(image_dir, 'image', 'png')
        image.save(filename)
        filename_prompt = self.get_next_filename(image_dir, 'image-prompt', 'txt')
        with open(filename_prompt, 'w', encoding='utf-8') as f:
            f.write(f"Image prompt: {prompt}")
        self.log("info", "reply.ngcimg", "Image saved.")
        self.response_count_image_ngc += 1
        await self.presence_update("idle")
        self.log("info", "reply.ngcimg", "AI image response parsing complete. Reply.ngcimg exit.")
        return filename
    
    #Check local service status
    async def service_check(self):
        #Testing AI system status
        self.log("debug", "main.testsvc", "Testing AI system status.")
        try:
            #Test query local AI service
            test_query = requests.get("http://192.168.0.175:5000/v1/models", timeout=3, headers={"Content-Type": "application/json"})
            if test_query.status_code == 200:
                self.local_ai = True
                self.log("info", "main.testsvc", "Local AI service is online, selected as default.")
        except requests.exceptions.ConnectionError:
            #Fallback to NGC AI service
            self.local_ai = False
            self.log("info", "main.testsvc", "Local AI service is offline, selected NGC as default.")
        except Exception as e:
            # Mark self.local_ai as True for other exceptions
            self.local_ai = True
            self.log("error", "main.testsvc", f"An unexpected error occurred: {str(e)}. Local AI service is still selected as default.")

    #Auto Check Service Status
    async def auto_service_check(self):
        while True:
            self.log("info", "main.testsvc", "Auto service check started.")
            await self.service_check()
            self.log("info", "main.testsvc", "Auto service check complete.")
            await asyncio.sleep(600)

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
    ai_status = "Local" if client.local_ai == True else "NGC"
    current_model = client.local_ai_model if client.local_ai == True else None
    current_model_ngc = client.ngc_ai_model
    return jsonify({
        'uptime': uptime,
        'uptime_unit': uptime_unit,
        'local_responses': client.response_count_local,
        'ngc_responses': client.response_count_ngc,
        'ngc_image_responses': client.response_count_image_ngc,
        'logging_mode': log_mode,
        'service_mode': ai_status,
        'current_model': current_model,
        'current_model_ngc': current_model_ngc
        })
    
@app.route('/api/service_mode', methods=['GET'])
def service_mode():
    if client.local_ai == True:
        return jsonify({'service_mode': 'Local'})
    else:
        return jsonify({'service_mode': 'NGC'})

@app.route('/api/current_model_local', methods=['GET'])
def current_model_local():
    if client.local_ai == True:
        return jsonify({'current_model': client.local_ai_model})
    else:
        return jsonify({'current_model': None})
    
@app.route('/api/ngc/models', methods=['GET'])
def ngc_models():
    return jsonify({'ngc_models': list(client.ngc_ai_invoke_url.keys())})

@app.route('/api/ngc/current_model', methods=['GET'])
def current_model_ngc():
    return jsonify({'current_model': client.ngc_ai_model})

@app.route('/api/ngc/load_model', methods=['POST'])
def load_model_ngc():
    model_name = request.json['model_name']
    client.ngc_ai_model = model_name
    return jsonify({'status': 'success'})

@app.route('/api/clear_context', methods=['POST'])
def clear_context():
    user_id = request.json['user_id']
    if client.local_ai == True:
        client.context_messages_local[user_id] = []
        client.context_messages_local[user_id] = client.context_messages_default.copy()
        client.context_messages_local_modified[user_id] = False
    else:
        client.context_messages[user_id] = []
        client.context_messages[user_id] = client.context_messages_default.copy()
        client.context_messages_modified[user_id] = False
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

@app.route('/api/service_update', methods=['POST'])
def service_update():
    service = request.json['service']
    if service == 'local':
        client.local_ai = True
    else:
        client.local_ai = False
    return jsonify({'status': 'success'})

@app.route('/stop', methods=['POST'])
def stop():
    client.close()
    os._exit(0)

def start_server():
    serve(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    
    start_bot()