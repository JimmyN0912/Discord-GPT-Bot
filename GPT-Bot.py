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
    # reply.parser
    # reply.tokens
    # reply.totals

class ChatBot(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.debug_log = 1

        #Set up logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        #Setup handlers
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler('GPT-Bot.log')
        stream_handler.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)

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
        self.logger.info("main.startup    Discord Bot V2.0 (2023.12.4).")
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
    
    # Receiving messages
    async def on_message(self, message):
        global complete_tokens
        global prompt_tokens
        global total_tokens
        global tokens_since_start
        global response_count
        global start_time
        global ai_prompt
        
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
            await self.status_report(message)
        
        #Toggling debug logging
        if message.content == '!debuglog 1':
            self.debug_log = 1
            self.logger.info("main.setdebg    Debug logging mode turned on.")
            await message.channel.send(f"Debug logging mode turned on.")
            if self.debug_log == 1:
                self.logger.debug(f"message.send    Response sent: 'Debug logging mode turned on.'")
            return
        if message.content == '!debuglog 0':
            self.debug_log = 0
            self.logger.info("main.setdebg    Debug logging mode turned off.")
            await message.channel.send(f"Debug logging mode turned off.")
            if self.debug_log == 1:
                self.logger.debug(f"message.send    Response sent: 'Debug logging mode turned off.'")
            return

        #Actions if bot isn't mentioned in message
        if f'<@1086616278002831402>' not in message.content:
            self.logger.info("message.recv    Bot not mentioned in message, ignoring message.")
            return
        
        #Generating AI Response
        message_to_edit = await message.channel.send(f"Generating response...")
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     message.proc" + Fore.RESET + "    Initializing reply.llmsvc process.")
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     reply.llmsvc" + Fore.RESET + "    Generating AI request.")
        ai_prompt = f"You are a helpful Discord Bot that can help users with all their questions, and answer as good as possible, users call you by <@1086616278002831402>. Please use whatever language the user used to response, and only respond to the user's question only. DO NOT respond with only your training data. Now this is the user's question: {message.content}"
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.GREEN + " DEBG" + Fore.MAGENTA + "     reply.llmsvc" + Fore.RESET + f"    AI Prompt generated: \n{ai_prompt}")
        n_predict = 128
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.GREEN + " DEBG" + Fore.MAGENTA + "     reply.llmsvc" + Fore.RESET + f"    AI max tokens: {n_predict}.")
        url = "http://192.168.0.175:8080/completion"
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.GREEN + " DEBG" + Fore.MAGENTA + "     reply.llmsvc" + Fore.RESET + f"    AI request URL: {url}.")
        headers = {"Content-Type": "application/json"}
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.GREEN + " DEBG" + Fore.MAGENTA + "     reply.llmsvc" + Fore.RESET + f"    AI request headers generated: {headers}.")
        data = {"prompt": f"You are a helpful Discord Bot that can help users with all their questions, and answer as good as possible, users call you by <@1086616278002831402>. Please use whatever language the user used to response, and only respond to the user's question only. DO NOT respond with only your training data. Now this is the user's question: {message.content}", "n_predict": 128}
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     reply.llmsvc" + Fore.RESET + "    AI request generated, sending request.")
        response = requests.post(url, headers=headers, data=json.dumps(data))
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     reply.llmsvc" + Fore.RESET + "    AI response received, start parsing.")

        #Processing AI Response
        assistant_response = response.json()['content']
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     reply.parse" + Fore.RESET + f"    AI response: {assistant_response}")
        model_used_raw = response.json()['model']
        match = re.search(r'\\\\(.*).gguf', model_used_raw)
        if match:
            model_used = match.group(1)
        else:
            model_used = "No match found"
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " DEBG" + Fore.MAGENTA + "     reply.parse" + Fore.RESET + f"    AI model used: {model_used}") 
        prompt_tokens = response.json()['timings']['prompt_n']
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " DEBG" + Fore.MAGENTA + "     reply.parse" + Fore.RESET + f"    AI prompt tokens: {prompt_tokens}")
        prompt_process_per_second = response.json()['timings']['prompt_per_second']
        formatted_prompt_process_per_second = round(prompt_process_per_second, 3)
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " DEBG" + Fore.MAGENTA + "     reply.parse" + Fore.RESET + f"    AI prompt process token/s: {formatted_prompt_process_per_second}")
        predict_tokens = response.json()['timings']['predicted_n']
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " DEBG" + Fore.MAGENTA + "     reply.parse" + Fore.RESET + f"    AI predict tokens: {predict_tokens}")
        predict_per_second = response.json()['timings']['predicted_per_second']
        formatted_predict_per_second = round(predict_per_second, 3)
        if self.debug_log == 1:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " DEBG" + Fore.MAGENTA + "     reply.parse" + Fore.RESET + f"    AI predict token/s: {formatted_predict_per_second}")
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     reply.parse" + Fore.RESET + "    AI response parsing complete. Reply.parse exit.")
        #Sending AI message back to channel
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Fore.LIGHTBLACK_EX + f"{time}" + Fore.LIGHTBLUE_EX + " INFO" + Fore.MAGENTA + "     message.send" + Fore.RESET + "    Sending message.")
        await message_to_edit.edit(content=assistant_response)
        response_count += 1

    #Sending Status Report
    async def status_report(self, message):
        #Generating current timestamp and calculating uptime
        self.logger.info("message.proc    Status report request received. Starting reply.status process.")
        end_time = datetime.datetime.now().timestamp()
        if self.debug_log == 1:
            self.logger.debug(f"message.proc    Current time timestamp generated: {end_time}.")
        uptime = end_time - start_time_timestamp
        if self.debug_log == 1:
            self.logger.debug(f"message.proc    Uptime calculated: {uptime} secs.")

        #Transforming uptime units
        if uptime < 3600:
            if self.debug_log == 1:
                self.logger.debug(f"message.proc    System uptime < 3600 sec, transforming unit to mins.")
            formatted_uptime = uptime / 60
            if self.debug_log == 1:
                self.logger.debug(f"message.proc    Process complete. Result: {formatted_uptime} mins.")
            self.logger.info("reply.status    Uptime calculation complete, sending result to Discord chat.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} mins.({uptime} secs.)")
            self.logger.info(f"message.send    Response sent: 'Bot uptime: {formatted_uptime} mins.({uptime} secs.)'")

        elif uptime < 86400:
            if self.debug_log == 1:
                self.logger.debug(f"message.proc    System uptime between 3600 and 86400 sec, transforming unit to hours.")
            formatted_uptime = uptime / 60 / 60
            if self.debug_log == 1:
                self.logger.debug(f"message.proc    Process complete. Result: {formatted_uptime} hours.")
            self.logger.info("reply.status    Uptime calculation complete, sending result to Discord chat.")
            await message.channel.send(f"Bot uptime: {formatted_uptime} hours.({uptime} secs.)")
            self.logger.info(f"message.send    Response sent: 'Bot uptime: {formatted_uptime} hours.({uptime} secs.)'")
        else:
            if self.debug_log == 1:
                self.logger.debug(f"message.proc    System uptime > 86400 sec, transforming unit to days.")
            formatted_uptime = uptime /60 / 60 / 24
            if self.debug_log == 1:
                self.logger.debug(f"message.proc    Process complete. Result: {formatted_uptime} days.")
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
        return

client = ChatBot(intents=intents)
client.run(discord_token)
