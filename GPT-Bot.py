import discord
import requests
import json
import nest_asyncio
import datetime
from colorama import Fore, init
import re
import logging

init(autoreset=True)
nest_asyncio.apply()
discord_token = str("MTA4NjYxNjI3ODAwMjgzMTQwMg.Gwuq8s.9kR8cIt1T8ahb1EGVQJcSwlfSyl4GnTrJiN0eU")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

complete_tokens = 0
prompt_tokens = 0
total_tokens = 0
tokens_since_start = 0
response_count = 0
startup_time = datetime.datetime.now().timestamp()

#Process names:
    # main.startup
    # main.setdebg
    # message.recv
    # message.proc
    # message.send
    # message.time
    # reply.status
    # reply.llmsvc

class ChatBot(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.debug_log = 1
        self.previous_prompt = None

        #Set up logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        #Setup handlers
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler('logs\GPT-Bot.log')
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
        global start_time_timestamp
        global start_time
        self.logger.info("main.startup    Discord Bot V2.2 (2023.12.8).")
        self.logger.info("main.startup    Discord Bot system starting...")
        start_time_timestamp = datetime.datetime.now().timestamp()
        if self.debug_log == 1:
            self.logger.debug(f"main.startup    start_time_timestamp generated: {start_time_timestamp}.")
        start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.debug_log == 1:
            self.logger.debug(f"main.startup    start_time generated: {start_time}.")
        self.logger.info("main.startup    System startup complete.")
        self.logger.info("main.startup    Startup thread exit.")

    # Discord.py module startup message
    async def on_ready(self):
        global time
        global bot_id
        bot_id = {self.user.id}
        if self.debug_log == 1:
            self.logger.debug(f"main.startup    Bot ID: {bot_id}.")
        self.logger.info("main.startup    Connection to Discord established successfully.")
        self.logger.info(f"main.startup    Connection thread exit.")
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        if self.debug_log == 1:
            self.logger.debug(f"main.startup    Bot presence set to 'Playing the waiting game'.")
    
    # Receiving messages
    async def on_message(self, message):
        global complete_tokens
        global prompt_tokens
        global total_tokens
        global tokens_since_start
        global response_count
        global start_time
        
        #Actions if message comes from user
        if message.author != self.user:
            self.logger.info(f"message.recv    Message Received: '{message.content}', from {message.author} in {message.channel}.")
            if self.debug_log == 1:
                self.logger.debug(f"message.recv    Message author not Bot, countinue processing.")
        
        #Actions if message comes from bot
        if message.author == self.user:
            if self.debug_log == 1:
                self.logger.debug(f"message.recv    Message author is Bot, ignoring message.")
                return
        
        #Actions if message is '!status'
        if message.content == '!status':
            self.logger.info("message.proc    Status report request received. Starting reply.status process.")
            await self.status_report(message)
        
        #Toggling debug logging
        if message.content == '!debuglog 1':
            self.debug_log = 1
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("main.setdebg    Debug logging mode turned on.")
            await message.channel.send(f"Debug logging mode turned on.")
            if self.debug_log == 1:
                self.logger.debug(f"message.send    Response sent: 'Debug logging mode turned on.'")
            return
        if message.content == '!debuglog 0':
            self.debug_log = 0
            self.logger.setLevel(logging.INFO)
            self.logger.info("main.setdebg    Debug logging mode turned off.")
            await message.channel.send(f"Debug logging mode turned off.")
            if self.debug_log == 1:
                self.logger.debug(f"message.send    Response sent: 'Debug logging mode turned off.'")
            return
        
        #Sending log file
        if message.content == '!getlogs':
            self.logger.info("message.proc    Log file request received, sending log file.")
            await message.channel.send(file=discord.File('logs\GPT-Bot.log'))
            self.logger.info("message.send    Log file sent.")
            return

        #Actions if bot isn't mentioned in message
        if f'<@1086616278002831402>' not in message.content:
            self.logger.info("message.recv    Bot not mentioned in message, ignoring message.")
            return
        
        #Actions if the message is the same
        if message.content == self.previous_prompt:
            self.logger.info("message.proc    Message is the same as previous prompt, ignoring message.")
            return

        #Generating AI Response
        message_to_edit = await message.channel.send(f"Generating response...")
        self.logger.info("message.proc    Starting reply.llmsvc process.")
        await self.ai_request(message.content)
        self.logger.info("message.proc    Starting reply.parser process.")

        #Processing AI Response
        await self.ai_response()

        #Sending AI message back to channel
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     message.send" + Fore.RESET + "    Sending message.")
        await message_to_edit.edit(content=assistant_response)
        response_count += 1

    #Sending Status Report
    async def status_report(self, message):
        #Changing bot presence to 'Streaming status report'
        await self.change_presence(activity=discord.Streaming(name="status report.", url="https://www.huggingface.co/"))
        if self.debug_log == 1:
            self.logger.debug(f"reply.status    Bot presence set to 'Streaming status report'.")
        
        #Generating current timestamp and calculating uptime
        end_time = datetime.datetime.now().timestamp()
        if self.debug_log == 1:
            self.logger.debug(f"reply.status    Current time timestamp generated: {end_time}.")
        uptime = end_time - start_time_timestamp
        if self.debug_log == 1:
            self.logger.debug(f"reply.status    Uptime calculated: {uptime} secs.")

        #Transforming uptime units
        if uptime < 3600:
            if self.debug_log == 1:
                self.logger.debug(f"reply.status    System uptime < 3600 sec, transforming unit to mins.")
            formatted_uptime = uptime / 60
            if self.debug_log == 1:
                self.logger.debug(f"reply.status    Process complete. Result: {formatted_uptime} mins.")
            self.logger.info("reply.status    Uptime calculation complete, sending result to Discord chat.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} mins.({uptime} secs.)")
            self.logger.info(f"message.send    Response sent: 'Bot uptime: {formatted_uptime} mins.({uptime} secs.)'")

        elif uptime < 86400:
            if self.debug_log == 1:
                self.logger.debug(f"reply.status    System uptime between 3600 and 86400 sec, transforming unit to hours.")
            formatted_uptime = uptime / 60 / 60
            if self.debug_log == 1:
                self.logger.debug(f"reply.status    Process complete. Result: {formatted_uptime} hours.")
            self.logger.info("reply.status    Uptime calculation complete, sending result to Discord chat.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} hours.({uptime} secs.)")
            self.logger.info(f"message.send    Response sent: 'Bot uptime: {formatted_uptime} hours.({uptime} secs.)'")
        else:
            if self.debug_log == 1:
                self.logger.debug(f"reply.status    System uptime > 86400 sec, transforming unit to days.")
            formatted_uptime = uptime /60 / 60 / 24
            if self.debug_log == 1:
                self.logger.debug(f"reply.status    Process complete. Result: {formatted_uptime} days.")
            self.logger.info("reply.status    Uptime calculation complete, sending result to Discord chat.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} days.({uptime} secs.)")
            self.logger.info(f"message.send   Response sent: 'Bot uptime: {formatted_uptime} days.({uptime} secs.)'")
        
        #Calculating total responses since start
        self.logger.debug(f"reply.status    Total responses since start: {response_count}.")
        self.logger.info("reply.status    Total responses since start calculation complete, sending result to Discord chat.")
        await message.channel.send(f"Total responses since start: {response_count}.")
        self.logger.info(f"message.send    Response sent: 'Total responses since start: {response_count}.'")

        #Display debug logging status
        if self.debug_log == 1:
            await message.channel.send(f"Debug logging is on.")
            self.logger.info(f"reply.status    Response sent: 'Debug logging is on.'")
        else:
            await message.channel.send(f"Debug logging is off.")
            self.logger.info(f"reply.status    Response sent: 'Debug logging is off.'")
        
        #Changing bot presence back to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        if self.debug_log == 1:
            self.logger.debug(f"reply.status    Bot presence set to 'Playing the waiting game'.")
        self.logger.info("reply.status    Status report sent, reply.status process exit.")
        return

    #Generating AI response
    async def ai_request(self, message):
        global response
        #Change bot presence to 'Streaming AI data'
        await self.change_presence(activity=discord.Streaming(name="AI data.", url="https://www.huggingface.co/"))
        self.previous_prompt = message
        if self.debug_log == 1:
            self.logger.debug(f"reply.llmsvc    Bot presence set to 'Streaming AI data'.")

        self.logger.info("reply.llmsvc    Generating AI request.")
        ai_prompt = f"You are an intelligent Discord Bot known as AI-Chat. Users refer to you by mentioning <@1086616278002831402>. When responding, use the same language as the user and focus solely on addressing their question. Avoid regurgitating training data. If the user asks, 'Who are you?' or similar, provide a brief introduction about yourself and your purpose in assisting users. Please do not engage in conversations that are not relevant to the user's question. If a conversation is not pertinent, politely point out that you cannot continue and suggest focusing on the original topic. Do not go off-topic without permission from the user. Only use AI-Chat as your name, do not include your id: </@1086616278002831402> in the reply. Now, here is the user's question: '{message}', please respond."
        if self.debug_log == 1:
            self.logger.debug(f"reply.llmsvc    AI Prompt generated: \n{ai_prompt}")
        max_tokens = 512
        if self.debug_log == 1:
            self.logger.debug(f"reply.llmsvc    AI max tokens: {max_tokens}.")
        url = "http://192.168.0.175:5000/v1/completions"
        if self.debug_log == 1:
            self.logger.debug(f"reply.llmsvc    AI request URL: {url}.")
        headers = {"Content-Type": "application/json"}
        if self.debug_log == 1:
            self.logger.debug(f"reply.llmsvc    AI request headers generated: {headers}.")
        data = {"prompt": ai_prompt, "max_tokens": max_tokens}
        self.logger.debug(f"reply.llmsvc    AI request data generated: {data}.")
        self.logger.info("reply.llmsvc    AI request generated, sending request.")
        response = requests.post(url, headers=headers, data=json.dumps(data))
        self.logger.info("reply.llmsvc    AI response received, start parsing.")
        self.logger.info("reply.llmsvc    reply.llmsvc process exit.")

    #Processing AI response
    async def ai_response(self):
        global assistant_response
        self.logger.info("reply.parser    Parsing AI response.")
        assistant_response = response.json()['choices'][0]['text']
        self.logger.info(f"reply.parser    AI response: {assistant_response}")
        model_used = response.json()['model']
        if self.debug_log == 1:
            self.logger.debug(f"reply.parser    AI model used: {model_used}")
        prompt_tokens = response.json()['usage']['prompt_tokens']
        if self.debug_log == 1:
            self.logger.debug(f"reply.parser    AI prompt tokens: {prompt_tokens}")
        completion_tokens = response.json()['usage']['completion_tokens']
        if self.debug_log == 1:
            self.logger.debug(f"reply.parser    AI predict tokens: {completion_tokens}")
        #Changing bot presence back to 'Playing the waiting game'
        await self.change_presence(activity=discord.Game(name="the waiting game."))
        if self.debug_log == 1:
            self.logger.debug(f"reply.parser    Bot presence set to 'Playing the waiting game'.")
        self.logger.info("reply.parser    AI response parsing complete. Reply.parse exit.")
        

client = ChatBot(intents=intents)
client.run(discord_token)
