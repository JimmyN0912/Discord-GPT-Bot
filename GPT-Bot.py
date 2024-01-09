import discord
import requests
import json
import nest_asyncio
import datetime
import logging
import sseclient
import Levenshtein
import os
import colorama
import hashlib

nest_asyncio.apply()
discord_token = str("MTA4NjYxNjI3ODAwMjgzMTQwMg.Gwuq8s.9kR8cIt1T8ahb1EGVQJcSwlfSyl4GnTrJiN0eU")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

#Global variables
prompt_tokens = 0
response_count = 0
start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
start_time_timestamp = datetime.datetime.now().timestamp()
bot_id = None
response_count = 0
local_ai = None
context_messages = [
    {
        "role": "user",
        "content": "You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. The following message is the user's message, please respond."
    }
]
stream_messages_hash = hashlib.md5(json.dumps(context_messages).encode('utf-8')).hexdigest()
context_messages_local = [
    {
        "role": "user",
        "content": "You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. The following message is the user's message, please respond."
    }
]
stream_messages_local_hash = hashlib.md5(json.dumps(context_messages_local).encode('utf-8')).hexdigest()

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
        self.debug_log = 1

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

        #Startup messages
        self.log("info", "main.startup", "Discord Bot V5.2 (2024.1.9).")
        self.log("info", "main.startup", "Discord Bot system starting...")
        self.log("info", "main.startup", f"start_time_timestamp generated: {start_time_timestamp}.")
        self.log("debug", "main.startup", f"start_time generated: {start_time}.")
        self.log("info", "main.startup", "System startup complete.")
        self.log("info", "main.startup", "Startup thread exit.")

        #Testing AI system status
        self.service_check(None)

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
            log_method(f"{color}{service}{colorama.Style.RESET_ALL}    {log_message}")
        else:
            self.logger.error(f"Invalid log level: {lvl}")

    # Discord.py module startup message
    async def on_ready(self):
        bot_id = {self.user.id}
        self.log("debug", "main.startup", f"Bot ID: {bot_id}.")
        self.log("info", "main.startup", "Connection to Discord established successfully.")
        self.log("info", "main.startup", "Connection thread exit.")
        #Changing bot presence to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        self.log("debug", "main.startup", "Bot presence set to 'Playing the waiting game'.")
    
    # Receiving messages
    async def on_message(self, message):
        
        #Commands Database
        commands = {
            '!status': self.status_report,
            '!debuglog 1': self.debuglogon,
            '!debuglog 0': self.debuglogoff,
            '!getlogs': self.getlogs,
            '!help': self.help,
            '!joke': self.send_joke,
            '!clear context': self.clear_context,
            '!context export': self.context_export,
            '!clear channel': self.clear_channel,
            '!model': self.model_info,
            '!service check': self.service_check,
         }

        #Announcing message
        self.log("info", "message.recv", f"Message Received: '{message.content}', from {message.author}, in {message.guild.name} / {message.channel.category.name} / {message.channel}.")

        #Actions if message comes from user
        if message.author != self.user:
            self.log("debug", "message.recv", "Message author not Bot, countinue processing.")
        
        #Actions if message comes from bot
        if message.author == self.user:
            self.log("debug", "message.recv", "Message author is Bot, ignoring message.")
            return

        #Identifying Commands
        if message.content.startswith('!'):
            self.log("info", "message.proc", "Message is a command, checking command database.")
            #Checking if command is in database
            for command, command_function in commands.items():
                if message.content == command:
                    await command_function(message)
                    return
            #Command not found, suggesting similar command
            similar_command = self.get_similar_command(message.content)
            await message.channel.send(f"Command not found. Did you mean '{similar_command}'?")
            
        #Actions if bot isn't mentioned in message
        if f'<@1086616278002831402>' not in message.content:
            self.log("info", "message.recv", "Bot not mentioned in message, ignoring message.")
            return
        

        #Generating AI Response

        if local_ai == True:
            if message.channel.category.name == 'text-to-text-local':
                if message.channel.name == 'stream':
                    message_to_edit = await message.channel.send(f"Generating response...")
                    await self.ai_response_streaming(message.content,message_to_edit)
                    return
                
                elif message.channel.name == 'context':
                    message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")
                    self.log("info", "message.proc", "Starting reply.llmctx process.")
                    await self.ai_context(message.content)
                    self.log("info", "message.proc", "Starting reply.parser process.")
                    await self.ai_context_response()
                    self.log("info", "message.send", "Sending message.")
                    try:
                        await message_to_edit.edit(content=assistant_response)
                    except discord.errors.HTTPException as e:
                        if e.code == 50035:  # Message is too long
                            await message_to_edit.delete()
                            chunks = [assistant_response[i:i+2000] for i in range(0, len(assistant_response), 2000)]
                            for chunk in chunks:
                                await message.channel.send(chunk)
                        else:
                            raise  # Re-raise the exception if it's not due to message length
                    
                elif message.channel.name == 'normal':
                    message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")
                    self.log("info", "message.proc", "Starting reply.llmsvc process.")
                    await self.ai_request(message.content)
                    self.log("info", "message.proc", "Starting reply.parser process.")
                    await self.ai_response()
                    self.log("info", "message.send", "Sending message.")
                    try:
                        await message_to_edit.edit(content=assistant_response)
                    except discord.errors.HTTPException as e:
                        if e.code == 50035:  # Message is too long
                            await message_to_edit.delete()
                            chunks = [assistant_response[i:i+2000] for i in range(0, len(assistant_response), 2000)]
                            for chunk in chunks:
                                await message.channel.send(chunk)
                        else:
                            raise  # Re-raise the exception if it's not due to message length
            
            if message.channel.category.name == 'text-to-text-ngc':
                if message.channel.name == 'context':
                    message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")
                    self.log("info", "message.proc", "Starting reply.ngcctx process.")
                    await self.ngc_ai_context(message.content)
                    self.log("info", "message.proc", "Starting reply.parser process.")
                    await self.ngc_ai_context_response(response)
                    self.log("info", "message.send", "Sending message.")
                    try:
                        await message_to_edit.edit(content=assistant_response)
                    except discord.errors.HTTPException as e:
                        if e.code == 50035:  # Message is too long
                            await message_to_edit.delete()
                            chunks = [assistant_response[i:i+2000] for i in range(0, len(assistant_response), 2000)]
                            for chunk in chunks:
                                await message.channel.send(chunk)
                        else:
                            raise  # Re-raise the exception if it's not due to message length

                elif message.channel.name == 'stream':
                    message_to_edit = await message.channel.send("Generating response...")
                    await self.ngc_ai_response_streaming(message.content,message_to_edit)
                    return

                elif message.channel.name == 'normal':
                    message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")
                    self.log("info", "message.proc", "Starting reply.ngcsvc process.")
                    await self.ngc_ai_request(message.content)
                    self.log("info", "message.proc", "Starting reply.parser process.")
                    await self.ngc_ai_response()
                    self.log("info", "message.send", "Sending message.")
                    try:
                        await message_to_edit.edit(content=assistant_response)
                    except discord.errors.HTTPException as e:
                        if e.code == 50035:  # Message is too long
                            await message_to_edit.delete()
                            chunks = [assistant_response[i:i+2000] for i in range(0, len(assistant_response), 2000)]
                            for chunk in chunks:
                                await message.channel.send(chunk)
                        else:
                            raise  # Re-raise the exception if it's not due to message length            
            
        else:
            if message.channel.category.name == 'text-to-text-ngc':
                if message.channel.name == 'context':
                    message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")
                    self.log("info", "message.proc", "Starting reply.ngcctx process.")
                    await self.ngc_ai_context(message.content)
                    self.log("info", "message.proc", "Starting reply.parser process.")
                    await self.ngc_ai_context_response(response)
                    self.log("info", "message.send", "Sending message.")
                    try:
                        await message_to_edit.edit(content=assistant_response)
                    except discord.errors.HTTPException as e:
                        if e.code == 50035:  # Message is too long
                            await message_to_edit.delete()
                            chunks = [assistant_response[i:i+2000] for i in range(0, len(assistant_response), 2000)]
                            for chunk in chunks:
                                await message.channel.send(chunk)
                        else:
                            raise  # Re-raise the exception if it's not due to message length
                elif message.channel.name == 'stream':
                    message_to_edit = await message.channel.send("Generating response...")
                    await self.ngc_ai_response_streaming(message.content,message_to_edit)
                    return

                elif message.channel.name == 'normal':
                    message_to_edit = await message.channel.send(f"Generating response...(Warning: This may take a while. If you don't want to wait, please use the 'stream' channel.)")
                    self.log("info", "message.proc", "Starting reply.ngcsvc process.")
                    await self.ngc_ai_request(message.content)
                    self.log("info", "message.proc", "Starting reply.parser process.")
                    await self.ngc_ai_response()
                    self.log("info", "message.send", "Sending message.")
                    try:
                        await message_to_edit.edit(content=assistant_response)
                    except discord.errors.HTTPException as e:
                        if e.code == 50035:  # Message is too long
                            await message_to_edit.delete()
                            chunks = [assistant_response[i:i+2000] for i in range(0, len(assistant_response), 2000)]
                            for chunk in chunks:
                                await message.channel.send(chunk)
                        else:
                            raise  # Re-raise the exception if it's not due to message length
            if message.channel.category.name == 'text-to-text-local':
                await message.channel.send(f"Local AI service is offline, please use the 'text-to-text-ngc' category.\nAlternatively, you can call '!service check' to check retest the AI service status.")
            
    #Sending Status Report
    async def status_report(self, message):
        self.log("info", "message.proc", "Status report request received. Starting reply.status process.")
        #Changing bot presence to 'Streaming status report'
        await self.change_presence(activity=discord.Streaming(name="status report.", url="https://www.huggingface.co/"))
        self.log("debug", "reply.status", "Bot presence set to 'Streaming status report.")
        
        #Generating current timestamp and calculating uptime
        end_time = datetime.datetime.now().timestamp()
        self.log("debug", "reply.status", f"Current time timestamp generated: {end_time}.")
        uptime = end_time - start_time_timestamp
        self.log("debug", "reply.status", f"Uptime calculated: {uptime} secs.")

        #Transforming uptime units
        #Uptime under 1 hour
        if uptime < 3600:
            self.log("debug", "reply.status", "System uptime < 3600 secs (1 hour), transforming unit to mins.")
            formatted_uptime = uptime / 60
            self.log("debug", "reply.status", f"Process complete. Result: {formatted_uptime} mins.")
            self.log("info", "reply.status", "Uptime calculation complete, sending result to Discord channel.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} mins.({uptime} secs.)")
            self.log("info", "message.send", f"Response sent: 'Bot uptime: {formatted_uptime} mins.({uptime} secs.)'")
        #Uptime between 1 hour and 24 hours
        elif uptime < 86400:
            self.log("debug", "reply.status", "System uptime between 3600 secs (1 hour) and 86400 secs (24 hours), transforming unit to hours.")
            formatted_uptime = uptime / 60 / 60
            self.log("debug", "reply.status", f"Process complete. Result: {formatted_uptime} hours.")
            self.log("info", "reply.status", "Uptime calculation complete, sending result to Discord chat.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} hours.({uptime} secs.)")
            self.log("info", "message.send", f"Response sent: 'Bot uptime: {formatted_uptime} hours.({uptime} secs.)'")
        #Uptime over 24 hours
        else:
            self.log("debug", "reply.status", "System uptime > 86400 sec(24 hours), transforming unit to days.")
            formatted_uptime = uptime / 60 / 60 / 24
            self.log("debug", "reply.status", f"Process complete. Result: {formatted_uptime} days.")
            self.log("info", "reply.status", "Uptime calculation complete, sending result to Discord chat.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} days.({uptime} secs.)")
            self.log("info", "message.send", f"Response sent: 'Bot uptime: {formatted_uptime} days.({uptime} secs.)'")
        
        #Calculating total responses since start
        self.log("debug", "reply.status", f"Total responses since start: {response_count}.")
        self.log("info", "reply.status", "Total responses since start calculation complete, sending result to Discord chat.")
        await message.channel.send(f"Total responses since start: {response_count}.")
        self.log("info", "message.send", f"Response sent: 'Total responses since start: {response_count}.'")

        #Display debug logging status
        if self.debug_log == 1:
            await message.channel.send(f"Debug logging is on.")
            self.log("info", "reply.status", "Response sent: 'Debug logging is on.'")
        else:
            await message.channel.send(f"Debug logging is off.")
            self.log("info", "reply.status", "Response sent: 'Debug logging is off.'")
        
        #Changing bot presence back to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        self.log("debug", "reply.status", "Bot presence set to 'Playing the waiting game'.")
        self.log("info", "reply.status", "Status report sent, reply.status process exit.")
        return

    #Generating AI Response - Local Mode
    async def ai_request(self, message):
        global response
        #Change bot presence to 'Streaming AI data'
        await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
        self.log("debug", "reply.llmsvc", "Bot presence set to 'Streaming AI data'.")
        self.log("info", "reply.llmsvc", "Generating AI request.")
        #Generating AI Prompt
        ai_prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond."
        self.log("debug", "reply.llmsvc", f"AI Prompt generated: \n{ai_prompt}")
        #Set max tokens
        max_tokens = 512
        self.log("debug", "reply.llmsvc", f"AI max tokens: {max_tokens}.")
        #Set request URL
        url = "http://192.168.0.175:5000/v1/completions"
        self.log("debug", "reply.llmsvc", f"AI request URL: {url}.")
        #Generate request headers
        headers = {"Content-Type": "application/json"}
        self.log("debug", "reply.llmsvc", f"AI request headers generated: {headers}.")
        #Combine request data
        data = {"prompt": ai_prompt, "max_tokens": max_tokens}
        self.log("debug", "reply.llmsvc", f"AI request data generated: {data}.")
        self.log("info", "reply.llmsvc", "AI request generated, sending request.")
        #Send request
        response = requests.post(url, headers=headers, data=json.dumps(data))
        self.log("info", "reply.llmsvc", "AI response received, start parsing.")
        self.log("info", "reply.llmsvc", "reply.llmsvc process exit.")

    #Processing AI Response - Local Mode
    async def ai_response(self):
        global assistant_response
        self.log("info", "reply.parser", "Parsing AI response.")
        #Extracting AI response
        assistant_response = response.json()['choices'][0]['text']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        #Extracting AI model used
        model_used = response.json()['model']
        self.log("debug", "reply.parser", f"AI model used: {model_used}")
        #Extracting AI prompt tokens
        prompt_tokens = response.json()['usage']['prompt_tokens']
        self.log("debug", "reply.parser", f"AI prompt tokens: {prompt_tokens}")
        #Extracting AI predict tokens
        completion_tokens = response.json()['usage']['completion_tokens']
        self.log("debug", "reply.parser", f"AI predict tokens: {completion_tokens}")
        #Changing bot presence back to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        self.log("debug", "reply.parser", "Bot presence set to 'Playing the waiting game'.")
        self.log("info", "reply.parser", "AI response parsing complete. Reply.parse exit.")
        
    #Streaming AI Response - Local Mode
    async def ai_response_streaming(self,message,message_to_edit):
        #Change bot presence to 'Streaming AI data'
        await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
        self.log("debug", "reply.llmsvc", "Bot presence set to 'Streaming AI data'.")
        self.log("info", "reply.llmsvc", "Generating AI request.")
        #Set request URL
        url = "http://192.168.0.175:5000/v1/chat/completions"
        self.log("debug", "reply.llmsvc", f"AI request URL: {url}.")
        #Generate request headers
        headers = {"Content-Type": "application/json"}
        self.log("debug", "reply.llmsvc", f"AI request headers generated: {headers}.")
        prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only reply to the user's question, do not continue onto other new ones. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond."
        #Combine request data
        data = {
            "mode": "instruct",
            "stream": True,
            "messages":[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        self.log("debug", "reply.llmsvc", f"AI request data generated: {data}")
        self.log("info", "reply.llmsvc", "AI request generated, sending request.")
        #Send request
        stream_response = requests.post(url, headers=headers, json=data, verify=False, stream=True)
        self.log("info", "reply.llmsvc", "AI response received, start parsing.")
        self.log("info", "reply.llmsvc", "Starting SSEClient to stream response.")
        #Start SSEClient to stream response
        client = sseclient.SSEClient(stream_response)
        new_content = ''
        for event in client.events():
            payload = json.loads(event.data)
            response_text = payload['choices'][0]['message']['content']
            if response_text.strip():
                new_content += response_text
                await message_to_edit.edit(content=new_content)
            else:
                pass
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

    #Debug Logging On
    async def debuglogon(self,message):
        self.debug_log = 1
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("main.setdebg    Debug logging mode turned on.")
        await message.channel.send(f"Debug logging mode turned on.")
        self.logger.debug(f"message.send    Response sent: 'Debug logging mode turned on.'")
        return
            
    #Debug Logging Off
    async def debuglogoff(self,message):
        self.debug_log = 0
        self.logger.setLevel(logging.INFO)
        self.log("debug", "main.setdebg", "Debug logging mode turned off.")
        await message.channel.send(f"Debug logging mode turned off.")
        self.log("debug", "message.send", f"Response sent: 'Debug logging mode turned off.'")
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
        await message.channel.send(f"Hello, I am AI-Chat.\nSome functions available:\n1.'!status' - Sends a status report.\n2.'!debuglog 1/0' - Turns on / off debug logging.\n3.'!getlogs' - Sends the log file.\n4.'!joke' - Sends a random joke.\n5.'!help' - Sends this help message.")
        await message.channel.send(f"6.'!clear context' - Clears the bot's message memory.\n7.'!context export' - Exports the 'Context' channel to a text file and sends it.\n8.'!clear channel' - Clears the current channel.\n9.'!model' - Sends the model information.\n10.'!service check' - Checks the AI service status.")
        self.log("info", "message.send", "Help message sent.")
        return

    #Provide Command Recommendations
    def get_similar_command(self,message):
        commands = ['!getlogs', '!status', '!debuglog 1', '!debuglog 0', '!help', '!joke', '!clear context']
        distances = [Levenshtein.distance(message, command) for command in commands]
        min_index = distances.index(min(distances))
        return commands[min_index]
    
    #Generating AI Response - NGC Mode
    async def ngc_ai_request(self,message):
        global assistant_response
        global response
        #Change bot presence to 'Streaming AI data'
        await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
        self.log("debug", "reply.ngcsvc", "Bot presence set to 'Streaming AI data'.")
        self.log("info", "reply.ngcsvc", "Generating AI request.")    
        #Set request URL
        invoke_url = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/0e349b44-440a-44e1-93e9-abe8dcb27158"
        self.log("debug", "reply.ngcsvc", f"AI request URL: {invoke_url}.")
        #Set fetch URL
        fetch_url_format = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/"
        self.log("debug", "reply.ngcsvc", f"AI fetch URL: {fetch_url_format}.")
        #Generate request headers
        headers = {
            "Authorization": "Bearer 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",
            "Accept": "application/json",
        }
        self.log("debug", "reply.ngcsvc", f"AI request headers generated: {headers}.")
        #Generate AI Prompt
        prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond."
        self.log("debug", "reply.ngcsvc", f"AI Prompt generated: \n{prompt}")
        #Generate request payload
        payload = {
            "messages": [
                {
                "content": prompt,
                "role": "user"
                }
            ],
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
            "seed": 42,
            "stream": False
        }
        self.log("debug", "reply.ngcsvc", f"AI request payload generated: {payload}.")
        #re-use connections
        session = requests.Session()
        self.log("info", "reply.ngcsvc", "AI request generated, sending request.")
        response = session.post(invoke_url, headers=headers, json=payload)
        #Check if response is ready
        while response.status_code == 202:
            request_id = response.headers.get("NVCF-REQID")
            fetch_url = fetch_url_format + request_id
            response = session.get(fetch_url, headers=headers)
        response.raise_for_status()
        self.log("info", "reply.ngcsvc", "AI response received, start reply.parser process.")

    #Processing AI Response - NGC Mode
    async def ngc_ai_response(self):
        global assistant_response
        self.log("info", "reply.parser", "Parsing AI response.")
        #Extracting AI response
        assistant_response = response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        #Extracting AI model used
        prompt_tokens = response.json()['usage']['prompt_tokens']
        self.log("debug", "reply.parser", f"AI prompt tokens: {prompt_tokens}")
        #Extracting AI predict tokens
        completion_tokens = response.json()['usage']['completion_tokens']
        self.log("debug", "reply.parser", f"AI predict tokens: {completion_tokens}")
        #Changing bot presence back to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        self.log("debug", "reply.parser", "Bot presence set to 'Playing the waiting game'.")
        self.log("info", "reply.parser", "AI response parsing complete. Reply.parser exit.")

    #Generating AI Response - NGC Mode - Context
    async def ngc_ai_context(self,message):
        global response
        #Change bot presence to 'Streaming AI data'
        await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
        self.log("debug", "reply.ngcsvc", "Bot presence set to 'Streaming AI data'.")
        self.log("info", "reply.ngcctx", "Generating AI request.")
        #Set request URL
        invoke_url = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/0e349b44-440a-44e1-93e9-abe8dcb27158"
        self.log("debug", "reply.ngcctx", f"AI request URL: {invoke_url}.")
        #Set fetch URL
        fetch_url_format = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/"
        self.log("debug", "reply.ngcctx", f"AI fetch URL: {fetch_url_format}.")
        #Generate request headers
        headers = {
            "Authorization": "Bearer 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",
            "Accept": "application/json",
        }
        self.log("debug", "reply.ngcctx", f"AI request headers generated: {headers}.")
        #Update message history
        context_messages.append({
            "role": "user",
            "content": message
        })
        self.log("debug", "reply.ngcctx", "Message history updated.")
        #Generate request payload
        payload = {
            "messages": context_messages,
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
            "seed": 42,
            "stream": False
        }
        self.log("debug", "reply.ngcctx", "AI request payload generated.")
        #re-use connections
        session = requests.Session()
        self.log("info", "reply.ngcctx", "AI request generated, sending request.")
        #Send request
        response = session.post(invoke_url, headers=headers, json=payload)
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

    #Processing AI Response - NGC Mode - Context
    async def ngc_ai_context_response(self,response):
        global assistant_response
        self.log("info", "reply.parser", "Parsing AI response.")
        #Extracting AI response
        assistant_response = response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        context_messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        self.log("debug", "reply.ngcctx", "Message history updated.")
        #Extracting AI prompt tokens
        prompt_tokens = response.json()['usage']['prompt_tokens']
        self.log("debug", "reply.parser", f"AI prompt tokens: {prompt_tokens}")
        #Extracting AI predict tokens
        completion_tokens = response.json()['usage']['completion_tokens']
        self.log("debug", "reply.parser", f"AI predict tokens: {completion_tokens}")
        #Changing bot presence back to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        self.log("debug", "reply.parser", "Bot presence set to 'Playing the waiting game'.")
        self.log("info", "reply.parser", "AI response parsing complete. Reply.parser exit.")

    #Clear Context
    async def clear_context(self,message):
        global context_messages
        self.log("info", "message.proc", "Clear context request received, clearing context.")
        #Reset message history
        context_messages = [
            {
                "role": "user",
                "content": "You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. The following message is the user's message, please respond."
            }
        ]
        self.logger.info("message.proc    Context cleared.")
        await message.channel.send(f"Context cleared.")

    #Export Context
    async def context_export(self,message):
        global context_messages
        self.log("info", "message.proc", "Context export request received, exporting context.")
        self.log("info", "message.proc", "Starting reply.ctxexp process.")
        stream_messages_current_hash = hashlib.md5(str(context_messages).encode('utf-8')).hexdigest()
        stream_messages_local_current_hash = hashlib.md5(str(context_messages_local).encode('utf-8')).hexdigest()
        self.log("debug", "reply.ctxexp", "Checking if directory exists.")
        context_dir = main_dir + '\context'
        if not os.path.exists(context_dir):
            self.log("debug", "reply.ctxexp", "Directory does not exist, creating directory.")
            os.makedirs(context_dir)
        file_name = self.get_next_filename(context_dir, 'context')
        with open(file_name, 'w') as f:
            if stream_messages_local_hash != stream_messages_local_current_hash:
                for messages in context_messages_local:
                    f.write(f"Role: {messages['role']}, Content: {messages['content']}\n")
            elif stream_messages_hash != stream_messages_current_hash:
                for messages in context_messages:
                    f.write(f"Role: {messages['role']}, Content: {messages['content']}\n")
            else:
                self.log("info", "reply.ctxexp", "No context changed, no export needed.")
                await message.channel.send(f"No context changed, no export needed.")
                return
            self.log("debug", "reply.ctxexp", "Context text file generated and saved.")
            await message.channel.send(file=discord.File(file_name))
            self.log("info", "message.send", "Context exported and sent.")
    
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
        await message.channel.purge()
        return

    #Generating AI Response - Local Mode - Context
    async def ai_context(self,message):
        global response
        #Change bot presence to 'Streaming AI data'
        await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
        self.log("debug", "reply.llmsvc", "Bot presence set to 'Streaming AI data'.")
        self.log("info", "reply.llmctx", "Generating AI request.")
        #Set request URL
        url = "http://192.168.0.175:5000/v1/chat/completions"
        self.log("debug", "reply.llmctx", f"AI request URL: {url}.")
        #Generate request headers
        headers = {"Content-Type": "application/json"}
        self.log("debug", "reply.llmctx", f"AI request headers generated: {headers}.")
        #Update message history
        context_messages_local.append({
            "role": "user",
            "content": message
        })
        self.log("debug", "reply.llmctx", "Message history updated.")
        #Combine request data
        data = {
            "mode": "instruct",
            "messages": context_messages_local,
            "max_tokens": 512
        }
        self.log("debug", "reply.llmctx", f"AI request data generated: {data}")
        self.log("info", "reply.llmctx", "AI request generated, sending request.")
        #Send request
        response = requests.post(url, headers=headers, json=data, verify=False)
        self.log("info", "reply.llmctx", "AI response received, start parsing.")
        self.log("info", "reply.llmctx", "reply.llmctx process exit.")

    #Processing AI Response - Local Mode - Context
    async def ai_context_response(self):
        global assistant_response
        self.log("info", "reply.parser", "Parsing AI response.")
        #Extracting AI response
        assistant_response = response.json()['choices'][0]['message']['content']
        self.log("info", "reply.parser", f"AI response: {assistant_response}")
        context_messages_local.append({
            "role": "assistant",
            "content": assistant_response
        })
        self.log("debug", "reply.llmctx", "Message history updated.")
        #Extracting AI model used
        model_used = response.json()['model']
        self.log("debug", "reply.parser", f"AI model used: {model_used}")
        #Extracting AI prompt tokens
        prompt_tokens = response.json()['usage']['prompt_tokens']
        self.log("debug", "reply.parser", f"AI prompt tokens: {prompt_tokens}")
        #Extracting AI predict tokens
        completion_tokens = response.json()['usage']['completion_tokens']
        self.log("debug", "reply.parser", f"AI predict tokens: {completion_tokens}")
        #Changing bot presence back to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        self.log("debug", "reply.parser", "Bot presence set to 'Playing the waiting game'.")
        self.log("info", "reply.parser", "AI response parsing complete. Reply.parse exit.")

    #Streaming AI Response - NGC Mode
    async def ngc_ai_response_streaming(self,message,message_to_edit):
        #Change bot presence to 'Streaming AI data'
        await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
        self.log("debug", "reply.ngcsvc", "Bot presence set to 'Streaming AI data'.")
        self.log("info", "reply.ngcsvc", "Generating AI request.")
        #Set request URL
        invoke_url = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/0e349b44-440a-44e1-93e9-abe8dcb27158"
        self.log("debug", "reply.ngcsvc", f"AI request URL: {invoke_url}.")
        headers = {
            "Authorization": "Bearer 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",
            "accept": "text/event-stream",
            "content-type": "application/json"
        }
        self.log("debug", "reply.ngcsvc", f"AI request headers generated:\n{headers}.")
        prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only reply to the user's question, do not continue onto other new ones. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond."
        self.log("debug", "reply.ngcsvc", f"AI Prompt generated: \n{prompt}")
        payload = {
            "messages": [
                {
                "content": prompt,
                "role": "user"
                }
            ],
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
            "seed": 42,
            "stream": True
        }
        self.log("debug", "reply.ngcsvc", f"AI request payload generated: {payload}.")
        response = requests.post(invoke_url, headers=headers, json=payload, verify=True, stream=True)
        assistant_response = ''
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line: #check if line is not empty
                    try:
                        json_line = json.loads(decoded_line.replace('data: ', '', 1))  # remove 'data: ' from the line
                        assistant_response += json_line['choices'][0]['delta']['content']
                        await message_to_edit.edit(content=assistant_response)
                    except json.decoder.JSONDecodeError:
                        if decoded_line == 'data: [DONE]':
                            self.log("info", "reply.ngcsvc", "AI response finished.")
                        continue

    #Listing current / available models
    async def model_info(self,message):
        self.log("info", "message.proc", "Model list request received, querying server.")
        #Set request URL
        url = "http://192.168.0.175:5000/v1/internal/model/info"
        self.log("debug", "message.proc", f"Model info request URL: {url}.")
        #Generate request headers
        headers = {"Content-Type": "application/json"}
        self.log("debug", "message.proc", f"Model info request headers generated: {headers}.")
        #Send request
        response = requests.get(url, headers=headers,verify=False)
        model_name = response.json()['model_name']
        self.log("info", "message.proc", f"Current model: {model_name}.")
        #Set request URL - 2
        url_2 = "http://192.168.0.175:5000/v1/internal/model/list"
        self.log("debug", "message.proc", f"Model list request URL: {url_2}.")
        #Send request - 2
        response_2 = requests.get(url_2, headers=headers,verify=False)
        models = response_2.json()['model_names']
        self.log("info", "message.proc", f"Model list: {models}.")
        numbered_models = "\n".join(f"{i+1}. {model}" for i, model in enumerate(models))
        await message.channel.send(f"Current loaded model:\n{model_name}\n\nAvailable models: \n{numbered_models}.")
        self.log("info", "message.send", "Model list sent.")

    #Load Model of Choice
    async def load_model(self,message,model_name):
        self.log("info", "message.proc", "Model load request received, starting model.loader process.")
        self.log("info", "model.loader", "Querying current model.")
        #Set request URL
        url = "http://192.168.0.175:5000/v1/internal/model/info"
        self.log("debug", "model.loader", f"Model info request URL: {url}.")
        #Generate request headers
        headers = {"Content-Type": "application/json"}
        self.log("debug", "model.loader", f"Model info request headers generated: {headers}.")
        #Send request
        response = requests.get(url, headers=headers,verify=False)
        current_model = response.json()['model_name']
        self.log("info", "model.loader", f"Current model: {current_model}.")
        self.log("info", "model.loader", f"Model selected: {model_name}.")
        if current_model == model_name:
            await message.channel.send(f"Model {model_name} already loaded.")
            self.log("info", "message.send", f"Model {model_name} already loaded.")
            return
        #Set request URL - 2
        url_2 = "http://192.168.0.175:5000/v1/internal/model/load"
        self.log("debug", "model.loader", f"Model load request URL: {url}.")
        self.log("debug", "model.loader", f"Model load request headers generated: {headers}.")
        #Generate request payload
        payload = {
            "model_name": model_name,
            "args": {"cpu": True}
        }
        self.log("debug", "model.loader", f"Model load request payload generated: \n{payload}.")
        #Send request
        response = requests.post(url_2, headers=headers, json=payload,verify=False)
        self.log("info", "model.loader", "Model load request sent.")
        if response.status_code == 200:
            await message.channel.send(f"Model {model_name} loaded.")
            self.log("info", "message.send", f"Model {model_name} loaded.")
        else:
            await message.channel.send(f"Model {model_name} failed to load.")
            self.log("info", "message.send", f"Model {model_name} failed to load.")

    #Check local service status
    async def service_check(self,message):
        #Testing AI system status
        global local_ai
        self.log("debug", "main.testsvc", "Testing AI system status.")
        try:
            #Test query local AI service
            test_query = requests.get("http://192.168.0.175:5000/v1/models", timeout=3, headers={"Content-Type": "application/json"})
            if test_query.status_code == 200:
                local_ai = True
                self.log("info", "main.testsvc", "Local AI service is online, selected as default.")
        except requests.exceptions.ConnectionError:
            #Fallback to NGC AI service
            local_ai = False
            self.log("info", "main.testsvc", "Local AI service is offline, selected NGC as default.")
        except Exception as e:
            # Mark local_ai as True for other exceptions
            local_ai = True
            self.log("error", "main.testsvc", f"An unexpected error occurred: {str(e)}. Local AI service is still selected as default.")
        if message != None:
            if local_ai == True:
                await message.channel.send(f"Local AI service is online, selected as default.")
                self.log("info", "message.send", f"Response sent: 'Local AI service is online, selected as default.'")
            else:
                await message.channel.send(f"Local AI service is offline, selected NGC as default.")
                self.log("info", "message.send", f"Response sent: 'Local AI service is offline, selected NGC as default.'")

client = ChatBot(intents=intents)
client.run(discord_token)
