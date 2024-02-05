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

nest_asyncio.apply()
discord_token = str("MTA4NjYxNjI3ODAwMjgzMTQwMg.Gwuq8s.9kR8cIt1T8ahb1EGVQJcSwlfSyl4GnTrJiN0eU")

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
    # model.loader

class ChatBot(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)

        #Set up logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger_sse = logging.getLogger('sseclient')
        self.logger_sse.setLevel(logging.ERROR)
        self.logger.propagate = False

        logging.addLevelName(logging.DEBUG, 'DEBG')

        #Setup handlers
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(log_dir + '\GPT-Bot.log')
        stream_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)

        #setup logging formats
        stream_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        stream_handler.setFormatter(stream_format)
        file_handler.setFormatter(file_format)

        #adding handlers
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(file_handler)

        #Variables
        self.response_count_local = 0
        self.response_count_ngc = 0
        self.start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.start_time_timestamp = datetime.datetime.now().timestamp()
        
        #Settings
        self.local_ai = None
        self.debug_log = 1
        self.local_ai_headers= {"Content-Type": "application/json"}
        self.local_ai_url= "http://192.168.0.175:5000/v1/completions"
        self.local_ai_context_url = "http://192.168.0.175:5000/v1/chat/completions"
        self.local_ai_model = None
        self.ngc_request_headers = {
            "Authorization": "Bearer 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",
            "Accept": "application/json",
        }
        self.ngc_request_headers_context = {
            "Authorization": "Bearer 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",
            "accept": "text/event-stream",
            "content-type": "application/json"
        }
        self.ngc_ai_invoke_url = {"llama-2-70b": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/0e349b44-440a-44e1-93e9-abe8dcb27158",
                                  "yi-34b": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/347fa3f3-d675-432c-b844-669ef8ee53df",
                                  "mixtral-8x7b-instruct": "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/8f4118ba-60a8-4e6b-8574-e38a4067a4a3"}
        self.ngc_ai_model = "llama-2-70b"
        self.ngc_ai_fetch_url_format = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/"
        self.ai_tokens = 512
        self.ai_temperature = 0.5
        self.load_model_args = defaultdict(lambda: {"cpu": True})
        self.load_model_args.update({
            "mistralai_Mistral-7B-Instruct-v0.2": {
                "cpu": True
            },
            "mistral-7b-instruct-v0.2.Q4_K_M.gguf": {
                "cpu": False,
                "n_gpu_layers": 35
            },
            "llama-2-7b-chat.Q4_K_M.gguf": {
                "cpu": False,
                "n_gpu_layers": 35
            },
            "llama-2-13b-chat.Q4_K_M.gguf": {
                "cpu": False,
                "n_gpu_layers": 43
            }
        })
        self.context_messages_default = [
            {
                "role": "user",
                "content": "You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. The following message is the user's message, please respond."
            }
        ]
        self.context_messages = self.context_messages_default.copy()
        self.context_messages_local = self.context_messages_default.copy()
        self.context_messages_modified = False
        self.context_messages_local_modified = False

        #Startup messages
        self.log("info", "main.startup", "Discord Bot V8.0 (2024.2.5).")
        self.log("info", "main.startup", "Discord Bot system starting...")
        self.log("info", "main.startup", f"start_time_timestamp generated: {self.start_time_timestamp}.")
        self.log("debug", "main.startup", f"start_time generated: {self.start_time}.")
        self.log("info", "main.startup", "System startup complete.")
        self.log("info", "main.startup", "Startup thread exit.")

    #Logging Function
    def log(self, lvl, service, log_message):
        log_method = getattr(self.logger, lvl, None)
        color = colorama.Fore.WHITE
        if service == "main.setdebg":
            color = colorama.Fore.RED
        elif service == "message.recv":
            color = colorama.Fore.LIGHTYELLOW_EX
        elif service == "reply.parser":
            color = colorama.Fore.LIGHTBLUE_EX
        elif service == "reply.llmsvc" or service == "reply.llmctx":
            color = colorama.Fore.LIGHTMAGENTA_EX
        elif service == "reply.ngcsvc" or service == "reply.ngcctx":
            color = colorama.Fore.GREEN
        if log_method is not None:
            log_message = self.clean_string(log_message)
            log_method(f"{color}{service}{colorama.Style.RESET_ALL}    {log_message}")
        else:
            self.logger.error(f"Invalid log level: {lvl}")

    #Remove non-ascii characters from log messages
    def clean_string(self, s):
        return s.encode('ascii', 'ignore').decode('ascii')

    # Discord.py module startup message
    async def on_ready(self):
        self.bot_id = self.user.id
        self.log("debug", "main.startup", f"Bot ID: {self.bot_id}.")
        self.log("info", "main.startup", "Connection to Discord established successfully.")
        self.log("info", "main.startup", "Connection thread exit.")
        await self.presence_update("idle")
        #Testing AI system status
        await self.service_check(None)
    
    # Receiving messages
    async def on_message(self, message):
        
        #Commands Database
        commands = {
            '!status': self.status_report,
            '!debuglog': self.debuglog,
            '!getlogs': self.getlogs,
            '!help': self.help,
            '!joke': self.send_joke,
            '!clear context': self.clear_context,
            '!context export': self.context_export,
            '!clear channel': self.clear_channel,
            '!models': self.model_info,
            '!service check': self.service_check,
            '!model load': self.load_model,
            '!model unload': self.unload_model
         }

        #Actions if message comes from bot
        if message.author == self.user:
            self.log("debug", "message.recv", "Message received. Author is Bot, ignoring message.")
            return

        #Announcing message
        self.log("info", "message.recv", f"Message Received: '{message.content}', from {message.author}, in {message.guild.name} / {message.channel.category.name} / {message.channel}.")
        
        #Identifying Commands
        if message.content.startswith('!'):
            self.log("info", "message.proc", "Message is a command, checking command database.")
            #Checking if command is in database
            for command, command_function in commands.items():
                if message.content.startswith(command):
                    await command_function(message)
                    return
            #Command not found, suggesting similar command
            similar_command = self.get_similar_command(message.content)
            await message.channel.send(f"Command not found. Did you mean '{similar_command}'?")
            return
            
        #Actions if bot isn't mentioned in message
        if f'<@1086616278002831402>' not in message.content:
            self.log("info", "message.recv", "Bot not mentioned in message, ignoring message.")
            return
        

        #Generating AI Response
        
        message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")

        if message.channel.category.name == 'text-to-text-local':
            #Local AI offline
            if self.local_ai == False:
                await message_to_edit.edit(content = f"Local AI service is offline, please use the 'text-to-text-ngc' category.\nAlternatively, you can call '!service check' to retest the AI service status if you think local AI should be online.")
                return
            
            if message.channel.name == 'stream':
                await self.ai_response_streaming(message.content,message_to_edit)
                return
                          
            else:
                context = True if message.channel.name == 'context' else False
                if context == True:
                    self.log("info", "message.proc", "Starting reply.llmctx process.")
                else:
                    self.log("info", "message.proc", "Starting reply.llmsvc process.")
                await self.ai_request(message.content,context)
                self.log("info", "message.proc", "Starting reply.parser process.")
                await self.ai_response(context)
                self.log("info", "message.send", "Sending message.")
                await message_to_edit.edit(content=f"*Model Used: {model_used}*")
                self.log("info", "message.send", f"Message sent. AI model used: {model_used}.")
                await self.send_message(message,assistant_response)
            
        if message.channel.category.name == 'text-to-text-ngc':
            if message.channel.name == 'stream':
                await self.ngc_ai_response_streaming(message.content,message_to_edit)
                return
            
            else:
                context = True if message.channel.name == 'context' else False
                if context == True:
                    self.log("info", "message.proc", "Starting reply.ngcctx process.")
                else:
                    self.log("info", "message.proc", "Starting reply.ngcsvc process.")
                await self.ngc_ai_request(message,context)
                self.log("info", "message.proc", "Starting reply.parser process.")
                await self.ngc_ai_response(context)
                self.log("info", "message.send", "Sending message.")
                await message_to_edit.edit(content=f"*Model Used: {self.ngc_ai_model}*")
                self.log("info", "message.send", f"Message sent. AI model used: {self.ngc_ai_model}.")
                await self.send_message(message,assistant_response)
            
    #Sending Status Report
    async def status_report(self, message):
        self.log("info", "message.proc", "Status report request received. Starting reply.status process.")
        await self.presence_update("status")
        
        #Generating current timestamp and calculating uptime
        end_time = datetime.datetime.now().timestamp()
        self.log("debug", "reply.status", f"Current time timestamp generated: {end_time}.")
        uptime = end_time - self.start_time_timestamp
        self.log("debug", "reply.status", f"Uptime calculated: {uptime} secs.")

        #Transforming uptime units
        #Uptime under 1 hour
        if uptime < 3600:
            self.log("debug", "reply.status", "System uptime < 3600 secs (1 hour), transforming unit to mins.")
            formatted_uptime = uptime / 60
            uptime_unit = 'mins'
        #Uptime between 1 hour and 24 hours
        elif uptime < 86400:
            self.log("debug", "reply.status", "System uptime between 3600 secs (1 hour) and 86400 secs (24 hours), transforming unit to hours.")
            formatted_uptime = uptime / 60 / 60
            uptime_unit = 'hours'
        #Uptime over 24 hours
        else:
            self.log("debug", "reply.status", "System uptime > 86400 sec(24 hours), transforming unit to days.")
            formatted_uptime = uptime / 60 / 60 / 24
            uptime_unit = 'days'
        
        self.log("debug", "reply.status", f"Process complete. Result: {formatted_uptime} {uptime_unit}.")
        self.log("info", "reply.status", "Uptime calculation complete, sending result to Discord channel.")
        
        #Calculating total responses since start
        self.log("debug", "reply.status", f"Total responses since start: {self.response_count_local + self.response_count_ngc}.")
        self.log("debug", "reply.status", f"Local responses since start: {self.response_count_local}.")
        self.log("debug", "reply.status", f"NGC responses since start: {self.response_count_ngc}.")

        #Get logging mode
        debug_status = 'on' if self.debug_log == 1 else 'off'
        self.log("debug", "reply.status", f"Debug logging is {debug_status}.")

        #Get AI service mode
        ai_status = 'Local' if self.local_ai == True else 'NGC'
        self.log("debug", "reply.status", f"AI service mode: {ai_status}.")

        #Get current AI model
        current_model_local = self.local_ai_model if self.local_ai == True else None
        current_model_ngc = self.ngc_ai_model 
        self.log("debug", "reply.status", f"Current local AI model: {current_model_local}. NGC model: {current_model_ngc}.")

        #Sending final status report
        await message.channel.send(f"Status:\n1. Bot ID: {self.bot_id}\n"+
                                   f"2. Bot Uptime: {formatted_uptime} {uptime_unit}.\n"+
                                   f"3. Total responses since start: {self.response_count_local + self.response_count_ngc}.\n"+
                                   f"4. Local responses since start: {self.response_count_local}.\n"+
                                   f"5. NGC responses since start: {self.response_count_ngc}.\n"+
                                   f"6. Debug logging is {debug_status}.\n"+
                                   f"7. AI service mode: {ai_status}.\n"+
                                   f"8. Current local AI model: {current_model_local}. NGC model: {current_model_ngc}.")
        
        await self.presence_update("idle")
        self.log("info", "reply.status", "Status report sent, reply.status process exit.")
        return

    #Generating AI Response - Local Mode
    async def ai_request(self, message,context):
        global response
        await self.presence_update("ai")
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
            #Update message history
            self.context_messages_local.append({
            "role": "user",
            "content": message
            })
            self.context_messages_local_modified = True
            self.log("debug", service, "Message history updated.")
            #Combine request data
            data = {
                "mode": "instruct",
                "messages": self.context_messages_local,
                "max_tokens": self.ai_tokens,
                "temperature": self.ai_temperature
            }
        else:
            #Set request URL
            url = self.local_ai_url
            self.log("debug", service, f"AI request URL: {url}.")
            #Generating AI Prompt
            ai_prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond. AI:"
            self.log("debug", service, f"AI Prompt generated.")
            #Combine request data
            data = {
            "prompt": ai_prompt,
            "max_tokens": max_tokens,
            "temperature": self.ai_temperature
            }
        self.log("debug", service, f"AI request data generated.")
        self.log("info", service, "AI request generated, sending request.")
        async with httpx.AsyncClient(verify=False,timeout=300) as client:
            response = await client.post(url, headers=headers, json=data)
        self.log("info", service, "AI response received, start parsing.")
        self.log("info", service, "reply.llmsvc process exit.")

    #Processing AI Response - Local Mode
    async def ai_response(self, context):
        global assistant_response
        global model_used
        self.log("info", "reply.parser", "Parsing AI response.")
        #Extracting AI response
        assistant_response = response.json()['choices'][0]['text'] if context == False else response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        if context == True:
            self.context_messages_local.append({
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
        prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only reply to the user's question, do not continue onto other new ones. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond."
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
                self.log("info", "reply.llmsvc", "Starting SSEClient to stream response.")
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

    #Generating Joke
    def get_joke(self):
        response = requests.get('https://official-joke-api.appspot.com/random_joke')
        joke = response.json()
        return f"{joke['setup']} - {joke['punchline']}"
    
    #Sending Joke
    async def send_joke(self,message):
        self.log("info", "message.proc", "Joke request received, sending joke.")
        joke = self.get_joke()
        await message.channel.send(joke)
        self.log("info", "message.send", "Joke sent.")
        return

    #Debug Logging On / Off
    async def debuglog(self,message):
        option = message.content.split(' ')[1]
        self.debug_log = 1 if option == 'on' else 0
        self.logger.setLevel(logging.DEBUG) if option == 'on' else self.logger.setLevel(logging.INFO)
        self.log("debug", "main.setdebg", f"Debug logging mode turned {option}.")
        await message.channel.send(f"Debug logging mode turned {option}.")
        return

    #Sending Logs File
    async def getlogs(self,message):
        self.log("info", "message.proc", "Log file request received, sending log file.")
        await message.channel.send(file=discord.File(log_dir + '\GPT-Bot.log'))
        self.log("info", "message.send", "Log file sent.")
        return

    #Sending Help Message
    async def help(self,message):
        self.log("info", "message.proc", "Help message request received, sending help message.")
        await message.channel.send(f"Hello, I am AI-Chat.\nSome functions available:\n1.'!status' - Sends a status report.\n2.'!debuglog on / off' - Turns on / off debug logging.\n3.'!getlogs' - Sends the log file.\n4.'!joke' - Sends a random joke.\n5.'!help' - Sends this help message.")
        await message.channel.send(f"6.'!clear context' - Clears the bot's message memory.\n7.'!context export' - Exports the 'Context' channel to a text file and sends it.\n8.'!clear channel' - Clears the current channel.\n9.'!models' - Sends the model information.\n10.'!service check' - Checks the AI service status.")
        await message.channel.send("11.'!model load {model_name}' - Loads the specified model.\n12.'!model unload' - Unloads the current loaded model.")
        self.log("info", "message.send", "Help message sent.")
        return

    #Provide Command Recommendations
    def get_similar_command(self,message):
        commands = ['!getlogs', '!status', '!debuglog 1', '!debuglog 0', '!help', '!joke', '!clear context']
        distances = [Levenshtein.distance(message, command) for command in commands]
        min_index = distances.index(min(distances))
        return commands[min_index]
    
    #Generating AI Response - NGC Mode
    async def ngc_ai_request(self,message,context):
        global response
        await self.presence_update("ai")
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
        self.log("debug", service, f"AI request headers generated: {headers}.")
        if context == False:
            #Generate AI Prompt
            prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message.content}', please respond."
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
        else:
            #Update message history
            self.context_messages.append({
                "role": "user",
                "content": message.content
            })
            self.context_messages_modified = True
            self.log("debug", service, "Message history updated.")
            #Generate request payload
            payload = {
                "messages": self.context_messages,
                "temperature": self.ai_temperature,
                "max_tokens": self.ai_tokens,
                "stream": False
            }
            #re-use connections
            session = requests.Session()
            self.log("info", "reply.ngcsvc", "AI request generated, sending request.")
            for _ in range(3):
                try:
                    response = session.post(invoke_url, headers=headers, json=payload)
                    break
                except requests.exceptions.ConnectionError:
                    time.sleep(3)
            if response.status_code == 500: #Message history too long
                self.log("debug", "reply.ngcctx", "Message history too long, please clear with '!clear context' and try again.")
                await message.channel.send(f"Message history too long, please clear with '!clear context' and try again.")
                return
            #Check if response is ready
            while response.status_code == 202:
                request_id = response.headers.get("NVCF-REQID")
                fetch_url = fetch_url_format + request_id
                response = session.get(fetch_url, headers=headers)
        response.raise_for_status()
        self.log("info", "reply.ngcsvc", "AI response received, start reply.parser process.")

    #Processing AI Response - NGC Mode
    async def ngc_ai_response(self, context):
        global assistant_response
        self.log("info", "reply.parser", "Parsing AI response.")
        #Extracting AI response
        assistant_response = response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        if context == True:
            self.context_messages.append({
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

    #Clear Context
    async def clear_context(self,message):
        self.log("info", "message.proc", "Clear context request received, clearing context.")
        #Reset message history
        if message.channel.category.name == 'text-to-text-local':
            self.context_messages_local = []
            self.context_messages_local = self.context_messages_default.copy()
            self.context_messages_local_modified = False
        else:
            self.context_messages = []
            self.context_messages = self.context_messages_default.copy()
            self.context_messages_modified = False
        self.logger.info("message.proc    Context cleared.")
        await message.channel.send(f"Context cleared.")

    #Export Context
    async def context_export(self,message):
        self.log("info", "message.proc", "Context export request received, exporting context.")
        self.log("info", "message.proc", "Starting reply.ctxexp process.")
        self.log("info", "reply.ctxexp", "Checking if context is modified.")
        if self.context_messages_modified == False and self.context_messages_local_modified == False:
            self.log("debug", "reply.ctxexp", "Context not modified, no export needed.")
            await message.channel.send(f"Context not modified, no export needed.")
            return
        self.log("debug", "reply.ctxexp", f"Context modified, exporting context.")
        self.log("debug", "reply.ctxexp", "Checking if directory exists.")
        context_dir = main_dir + '\context'
        if not os.path.exists(context_dir):
            self.log("debug", "reply.ctxexp", "Directory does not exist, creating directory.")
            os.makedirs(context_dir)
        file_name = self.get_next_filename(context_dir, 'context')
        with open(file_name, 'w', encoding='utf-8') as f:
            if self.context_messages_local_modified == True:
                f.write("Local Context:\n")
                for messages in self.context_messages_local:
                    f.write(f"{messages['role']}: {messages['content']}\n\n")
            if self.context_messages_modified == True:
                f.write("NGC Context:\n")
                for messages in self.context_messages:
                    f.write(f"{messages['role']}: {messages['content']}\n\n")
        self.log("debug", "reply.ctxexp", "Context exported, sending file.")
        await message.channel.send(file=discord.File(file_name))
        self.log("info", "reply.ctxexp", "Context export complete, reply.ctxexp process exit.")
    
    #Get next filename (for context export)
    def get_next_filename(self, directory, base_filename):
        i = 1
        while True:
            filename = f"{directory}/{base_filename}-{i}.txt"
            if not os.path.exists(filename):
                return filename
            i += 1

    #Clears Channel
    async def clear_channel(self,message):
        self.log("info", "message.proc", "Clear channel request received, clearing channel.")
        await message.channel.purge()
        self.log("info", "message.proc", "Channel cleared.")
        return

    #Streaming AI Response - NGC Mode
    async def ngc_ai_response_streaming(self,message,message_to_edit):
        await self.presence_update("ai")
        self.log("info", "reply.ngcsvc", "Generating AI request.")
        #Set request URL
        invoke_url = self.ngc_ai_invoke_url[self.ngc_ai_model]
        self.log("debug", "reply.ngcsvc", f"AI model: {self.ngc_ai_model} / Request URL: {invoke_url}.")
        headers = self.ngc_request_headers_context
        self.log("debug", "reply.ngcsvc", f"AI request headers generated:\n{headers}.")
        prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only reply to the user's question, do not continue onto other new ones. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond."
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

    #Listing current / available models
    async def model_info(self,message):
        if message.channel.category.name == 'text-to-text-local':
            self.log("info", "message.proc", "Model list request received, querying server.")
            #Set request URL
            url = "http://192.168.0.175:5000/v1/internal/model/info"
            self.log("debug", "message.proc", f"Model info request URL: {url}.")
            #Generate request headers
            headers = {"Content-Type": "application/json"}
            self.log("debug", "message.proc", f"Model info request headers generated: {headers}.")
            #Send request
            response = requests.get(url, headers=headers,verify=False)
            self.local_ai_model = response.json()['model_name']
            self.log("info", "message.proc", f"Current model: {self.local_ai_model}.")
            #Set request URL - 2
            url_2 = "http://192.168.0.175:5000/v1/internal/model/list"
            self.log("debug", "message.proc", f"Model list request URL: {url_2}.")
            #Send request - 2
            response_2 = requests.get(url_2, headers=headers,verify=False)
            models = response_2.json()['model_names']
            self.log("info", "message.proc", f"Model list: {models}.")
            numbered_models = "\n".join(f"{i}. {model}" for i, model in enumerate(models,1))
            await message.channel.send(f"Current loaded model:\n{self.local_ai_model}\n\nAvailable models: \n{numbered_models}.")
            self.log("info", "message.send", "Model list sent.")
        else:
            self.log("info", "message.proc", f"Current model:\n{self.ngc_ai_model}")
            numbered_models = "\n".join(f"{i}. {key}" for i, key in enumerate(self.ngc_ai_invoke_url,1))
            await message.channel.send(f"Current loaded model:\n{self.ngc_ai_model}\n\nAvailable models: \n{numbered_models}.")
            
    #Load Model of Choice
    async def load_model(self, message):
        if message.channel.category.name == 'text-to-text-local':
            self.log("info", "message.proc", "Model load request received, starting model.loader process.")
            self.log("info", "model.loader", "Querying current model.")
            # Set request URL
            url = "http://192.168.0.175:5000/v1/internal/model/info"
            self.log("debug", "model.loader", f"Model info request URL: {url}.")
            # Generate request headers
            headers = self.local_ai_headers
            self.log("debug", "model.loader", f"Model info request headers generated: {headers}.")
            # Send request
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, verify=False)
                current_model = response.json()['model_name']
            self.log("info", "model.loader", f"Current model: {current_model}.")
            model_name = message.content.split(' ')[2]
            self.log("info", "model.loader", f"Model selected: {model_name}.")
            if model_name == ' ':
                await message.channel.send(f"Model name cannot be empty.")
                self.log("info", "message.send", f"Response sent: 'Model name cannot be empty.'")
                return
            if current_model == model_name:
                await message.channel.send(f"Model {model_name} already loaded.")
                self.log("info", "message.send", f"Model {model_name} already loaded.")
                return
            info_message = await message.channel.send(f"Loading model {model_name}, please wait...")
            # Set request URL - 2
            url_2 = "http://192.168.0.175:5000/v1/internal/model/load"
            self.log("debug", "model.loader", f"Model load request URL: {url}.")
            self.log("debug", "model.loader", f"Model load request headers generated: {headers}.")
            # Generate request payload
            payload = {
                "model_name": model_name,
                "args": self.load_model_args[model_name]
            }
            self.log("debug", "model.loader", f"Model load request payload generated: \n{payload}.")
            # Send request - 2
            async with httpx.AsyncClient(verify=False, timeout=60) as client:
                response = await client.post(url_2, headers=headers, json=payload, verify=False)
                self.log("info", "model.loader", "Model load request sent.")
                if response.status_code == 200:
                    await info_message.edit(content=f"Model {model_name} loaded.")
                    self.log("info", "model.loader", f"Model {model_name} loaded.")
                else:
                    await info_message.edit(content=f"Model {model_name} failed to load.")
                    self.log("info", "model.loader", f"Model {model_name} failed to load.")
        else:
            self.log("info", "message.proc", "Model load request received, starting model.loader process.")
            self.log("info", "model.loader", f"Current model:{self.ngc_ai_model}")
            model_name = message.content.split(' ')[2]
            self.log("info", "model.loader", f"Model selected: {model_name}.")
            if model_name == ' ':
                await message.channel.send(f"Model name cannot be empty.")
                self.log("info", "message.send", f"Response sent: 'Model name cannot be empty.'")
                return
            if self.ngc_ai_model == model_name:
                await message.channel.send(f"Model {model_name} already loaded.")
                self.log("info", "message.send", f"Model {model_name} already loaded.")
                return
            self.ngc_ai_model = model_name
            await message.channel.send(f"Model {model_name} loaded.")

    #Check local service status
    async def service_check(self,message):
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
        if message != None:
            if self.local_ai == True:
                await message.channel.send(f"Local AI service is online, selected as default.")
                self.log("info", "message.send", f"Response sent: 'Local AI service is online, selected as default.'")
            else:
                await message.channel.send(f"Local AI service is offline, selected NGC as default.")
                self.log("info", "message.send", f"Response sent: 'Local AI service is offline, selected NGC as default.'")

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

    #Unload Model
    async def unload_model(self,message):
        self.log("info", "message.proc", "Model unload request received, starting model.loader process.")
        self.log("info", "model.loader", "Querying current model.")
        #Set request URL
        url = "http://192.168.0.175:5000/v1/internal/model/info"
        self.log("debug", "model.loader", f"Model info request URL: {url}.")
        #Generate request headers
        headers = self.local_ai_headers
        self.log("debug", "model.loader", f"Model info request headers generated: {headers}.")
        #Send request
        response = requests.get(url, headers=headers,verify=False)
        current_model = response.json()['model_name']
        self.log("info", "model.loader", f"Current model: {current_model}.")
        self.log("info", "model.loader", "Unloading model.")
        #Set request URL - 2
        url_2 = "http://192.168.0.175:5000/v1/internal/model/unload"
        self.log("debug", "model.loader", f"Model unload request URL: {url}.")
        self.log("debug", "model.loader", f"Model unload request headers generated: {headers}.")
        #Send request - 2
        response = requests.post(url_2, headers=headers,verify=False)
        self.log("info", "model.loader", "Model unload request sent.")
        if response.status_code == 200:
            await message.channel.send(f"Model {current_model} unloaded.")
            self.log("info", "model.loader", f"Model {current_model} unloaded.")
        else:
            await message.channel.send(f"Model {current_model} failed to unload.")
            self.log("info", "model.loader", f"Model {current_model} failed to unload.")
            await message.channel.send(f"Error: {response.text}")
            self.log("info", "model.loader", f"Error: {response.text}")

client = ChatBot(intents=intents)
client.run(discord_token)
