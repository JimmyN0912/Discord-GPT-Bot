import discord
import os
from dotenv import load_dotenv
from typing import Literal, Optional
import requests
from collections import defaultdict
import subprocess
import logging

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

### Logging ###

#Setup logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_dir = "C:\GPT-Bot\logs"

#Setup handlers
stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler(log_dir + '\slash-command.log', "a", "utf-8")
stream_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

#Setup logging formats
stream_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
stream_handler.setFormatter(stream_format)
file_handler.setFormatter(file_format)

#Adding handlers
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

#Logging Function
def log(lvl, service, log_message):
    log_method = getattr(logger, lvl, None)
    if log_method is not None:
        log_message = log_message.encode('utf-8').decode('utf-8')
        log_method(f"{service}   {log_message}")
    else:
        logger.error(f"Invalid log level: {lvl}")

#Logging service names
    #main.startup
    #proc.getlogs
    #proc.clrchan
    #proc.mdlopts
    #proc.botstop
    #proc.botupda
    #proc.botrest
    #proc.clrcont
    #proc.ctxexpo
    #proc.status
    #proc.debglog
    #proc.chcksvc
    #proc.imgrank
    #proc.annomsg
    #proc.peropts

### Global Variables ###
headers = {"Content-Type": "application/json"}
url_bot_text_service_mode = "http://localhost:5000/api/text_service_mode"
url_bot_clear_context = "http://localhost:5000/api/clear_context"
url_bot_context_export = "http://localhost:5000/api/context_export"
url_bot_status = "http://localhost:5000/api/status"
url_bot_debug_log = "http://localhost:5000/api/debug_log"
url_bot_image_rank = "http://localhost:5000/api/imagegen_rank"
url_bot_personality_mode = "http://localhost:5000/api/personality_mode"
url_bot_stop = "http://localhost:5000/stop"
url_bot_pause = "http://localhost:5000/api/bot_mode"
url_server_test = "http://192.168.0.175:5000/v1/models"
url_image_server_test = "http://192.168.0.175:7861/internal/ping"
url_server_model_info = "http://192.168.0.175:5000/v1/internal/model/info"
url_server_list_model = "http://192.168.0.175:5000/v1/internal/model/list"
url_server_load_model = "http://192.168.0.175:5000/v1/internal/model/load"
url_server_unload_model = "http://192.168.0.175:5000/v1/internal/model/unload"
load_model_args = defaultdict(lambda: {"cpu": True})
load_model_args.update({
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
bot_online = True

### Command List ###
# 1. Get Logs
# 2. Clear Channel
# 3. Model Options - Info, Load, Unload, Reload
# 4. Stop Bot
# 5. Update Bot
# 6. Restart Bot
# 7. Clear Context
# 8. Context Export
# 9. Status
# 10.Debug Logging
# 11.Image Generation Rank
# 12.Announce Message
# 13.Pause Bot
# 14.Personality AI mode

#Command: Get Logs
@tree.command(
    name="getlogs",
    description="Sends the log file of the script.",
)
async def get_logs(interaction: discord.Interaction):
    if bot_online == True:
        log("info", "proc.getlogs", "Get logs command received. Loading logs...")
        await interaction.response.send_message(file=discord.File("C:\GPT-Bot\logs\GPT-Bot.log"))
        log("info", "proc.getlogs", "Log file sent.")
    else:
        return

#Command: Clear Channel
@tree.command(
    name="clearchannel",
    description="Clears the channel.",
)
async def clear_channel(interaction: discord.Interaction):
    if bot_online == True:
        log("info", "proc.clrchan", "Clear channel command received. Clearing channel...")
        await interaction.response.send_message("Clearing channel...")
        await interaction.channel.purge()
        log("info", "proc.clrchan", "Channel cleared.")
    else:
        return

#Command: Model Options
@tree.command(
    name="model",
    description="Options: info, load, unload, reload",
)
async def model_options(interaction: discord.Interaction, option: Literal["info", "load", "unload"], model_name: Optional[str] = None):
    if bot_online == True:
        log("info", "proc.mdlopts", "Model option command received.")
        await interaction.response.defer()
        if option == "info":
            log("debug", "proc.mdlopts", "Model info requested.")
            service_mode = requests.get(url_bot_text_service_mode, headers=headers, verify=False).json()['service_mode']
            log("info", "proc.mdlopts", f"Bot service mode: {service_mode}.")
            if service_mode == "Online":
                log("debug", "proc.mdlopts", "Querying current loaded model.")
                current_model = requests.get(url_server_model_info, headers=headers, verify=False).json()['model_name']
                log("debug", "proc.mdlopts", "Querying available models.")
                model_names = requests.get(url_server_list_model, headers=headers, verify=False).json()['model_names']
                model_list = "\n".join(f"{i}. {model}" for i, model in enumerate(model_names,1))
                log("info", "proc.mdlopts", "Processing complete. Sending model info.")
                await interaction.followup.send(content = f"Current Model Server: {service_mode}\n\nCurrent Model: {current_model}\n\nAvailable Models:\n{model_list}")
            else:
                log("info", "proc.mdlopts", "AI service offline. Rejecting request.")
                await interaction.followup.send(content = "AI service offline. Please try again later.")
        elif option == "load":
            log("debug", "proc.mdlopts", f"Model load requested. Model selected: {model_name}.")
            if model_name is None:
                log("warning", "proc.mdlopts", "Model name not specified. Rejecting request.")
                await interaction.followup.send("Please specify a model name.")
                return
            service_mode = requests.get(url_bot_text_service_mode, headers=headers, verify=False).json()['service_mode']
            log("info", "proc.mdlopts", f"Bot service mode: {service_mode}.")
            if service_mode == "Online":
                log("debug", "proc.mdlopts", "Querying current loaded model.")
                current_model = requests.get(url_server_model_info, headers=headers, verify=False).json()['model_name']
                if model_name == current_model:
                    log("warning", "proc.mdlopts", "Model is already loaded. Rejecting request.")
                    await interaction.followup.send(content = f"Model {model_name} is already loaded.")
                    return
                message = await interaction.followup.send(content = f"Loading Model: {model_name}")
                payload = {"model_name": model_name, "args": load_model_args[model_name]}
                log("debug", "proc.mdlopts", "Sending request to load model.")
                response = requests.post(url_server_load_model, json=payload, headers=headers, verify=False)
                if response.status_code == 200:
                    log("info", "proc.mdlopts", f"Model {model_name} loaded.")
                    await message.edit(content = f"Model Loaded: {model_name}")
                else:
                    log("warning", "proc.mdlopts", f"Failed to load model: {model_name}.")
                    await message.edit(content = f"Failed to load model: {model_name}")
            else:
                log("info", "proc.mdlopts", "AI service offline. Rejecting request.")
                await interaction.followup.send(content = "AI service offline. Please try again later.")
        elif option == "unload":
            log("debug", "proc.mdlopts", "Model unload requested.")
            service_mode = requests.get(url_bot_text_service_mode, headers=headers, verify=False).json()['service_mode']
            log("info", "proc.mdlopts", f"Bot service mode: {service_mode}.")
            if service_mode == "Online":
                log("debug", "proc.mdlopts", "Sending request to unload model.")
                response = requests.post(url_server_unload_model, headers=headers, verify=False)
                if response.status_code == 200:
                    log("info", "proc.mdlopts", "Model Unloaded.")
                    await interaction.followup.send(content = "Model Unloaded")
                else:
                    log("warning", "proc.mdlopts", "Failed to unload model.")
                    await interaction.followup.send(content = "Failed to unload model")
            else:
                log("info", "proc.mdlopts", "AI service offline. Rejecting request.")
                await interaction.followup.send(content = "AI service offline. Please try again later.")
    else:
        return

#Command: Stop Bot
@tree.command(
    name="stopbot",
    description="Stops the bot.",
)
async def stop_bot(interaction: discord.Interaction):
    if bot_online == True:
        log("info", "proc.botstop", "Stop bot command received.")
        if interaction.user.name == "jimmyn3577":
            log("info", "proc.botstop", "User authorized. Stopping bot...")
            await interaction.response.send_message("Stopping bot...")
            try:
                log("debug", "proc.botstop", "Sending request to stop bot.")
                with requests.Session() as session:
                    session.post(url_bot_stop, headers=headers, verify=False)
            except Exception:
                pass
            finally:
                session.close()
            log("debug", "proc.botstop", "Stopping command processer.")
            await client.close()
        else:
            log("warning", "proc.botstop", "User not authorized. Rejecting request.")
            await interaction.response.send_message("You do not have permission to stop the bot.")
    else:
        return

#Command: Update Bot
@tree.command(
    name="updatebot",
    description="Updates the bot.",
)
async def update_bot(interaction: discord.Interaction):
    if bot_online == True:
        log("info", "proc.botupda", "Update bot command received.")
        if interaction.user.name == "jimmyn3577":
            log("info", "proc.botupda", "User authorized. Updating bot...")
            await interaction.response.send_message("Updating bot...")
            try:
                log("debug", "proc.botupda", "Sending request to stop bot.")
                requests.post(url_bot_stop, headers=headers, verify=False)
            except requests.exceptions.ConnectionError:
                pass
            log("debug", "proc.botupda", "Starting update process.")
            subprocess.Popen(["python", "update.py"])
            log("debug", "proc.botupda", "Update complete. Restarting...")
            await client.close()
        else:
            log("warning", "proc.botupda", "User not authorized. Rejecting request.")
            await interaction.response.send_message("You do not have permission to update the bot.")
    else:
        return

#Command: Restart Bot
@tree.command(
    name="restartbot",
    description="Restarts the bot.",
)
async def restart_bot(interaction: discord.Interaction):
    if bot_online == True:
        log("info", "proc.botrest", "Restart bot command received.")
        if interaction.user.name == "jimmyn3577":
            log("info", "proc.botrest", "User authorized. Restarting bot...")
            await interaction.response.send_message("Restarting bot...")
            try:
                log("debug", "proc.botrest", "Sending request to stop bot.")
                requests.post(url_bot_stop, headers=headers, verify=False)
            except requests.exceptions.ConnectionError:
                pass
            log("debug", "proc.botrest", "Starting restart process.")
            subprocess.Popen(["python", "restart.py"])
            await client.close()
        else:
            log("warning", "proc.botrest", "User not authorized. Rejecting request.")
            await interaction.response.send_message("You do not have permission to restart the bot.")
    else:
        return

#Command: Clear Context
@tree.command(
    name="clearcontext",
    description="Clears the context history.",
)
async def clear_context(interaction: discord.Interaction):
    if bot_online == True:
        await interaction.response.defer()
        log("info", "proc.clrcont", "Clear context command received.")
        message = await interaction.followup.send(content = "Clearing context...")
        r = requests.post(url_bot_clear_context, headers=headers, json={"user_id" : interaction.user.id,"channel_id": interaction.channel.id}, verify=False)
        if r.status_code == 200:
            await message.edit(content = "Context cleared.")
        else:
            await message.edit(content = "This channel has no context history.")
    else:
        return

#Command: Context Export
@tree.command(
    name="contextexport",
    description="Exports the context history.",
)
async def context_export(interaction: discord.Interaction):
    if bot_online == True:
        await interaction.response.defer()
        log("info", "proc.ctxexpo", "Context export command received.")
        message = await interaction.followup.send(content = "Exporting context...")
        request_result = requests.post(url_bot_context_export, headers=headers, json={"user_id" : interaction.user.id}, verify=False).json()
        if request_result["status"] == "no_export":
            log("warning", "proc.ctxexpo", "Context not modified. No context to export.")
            await message.edit(content = "Context not modified. No context to export.")
        else:
            log("info", "proc.ctxexpo", "Context exported. Sending file...")
            await message.edit(content = "Context exported:")
            await interaction.channel.send(file = discord.File(request_result["file_name"]))
    else:
        return
    
#Command: Status
@tree.command(
    name="status",
    description="Displays the status of the bot.",
)
async def status(interaction: discord.Interaction):
    if bot_online == True:
        await interaction.response.defer()
        log("info", "proc.status", "Status command received.")
        status_report_data = requests.get(url_bot_status, headers=headers, verify=False).json()
        log("info", "proc.status", "Sending status report.")
        embed = discord.Embed(title="Status Report", color=int('FE9900', 16))
        embed.add_field(name="AI-Chat Version", value=status_report_data['version'], inline=True)
        embed.add_field(name="Version Date", value=status_report_data['version_date'], inline=True)
        embed.add_field(name="Bot Uptime", value=f"{status_report_data['uptime']} {status_report_data['uptime_unit']}", inline=True)
        embed.add_field(name="Text Responses", value=status_report_data['text_responses'], inline=True)
        embed.add_field(name="Gemini Text Responses", value=status_report_data['gemini_responses'], inline=True)
        embed.add_field(name="Image Responses", value=status_report_data['image_responses'], inline=True)
        embed.add_field(name="Debug Logging", value=status_report_data['logging_mode'], inline=False)
        embed.add_field(name="AI Text Service Status", value=status_report_data['text_service_status'], inline=True)
        embed.add_field(name="Current Local AI Model", value=status_report_data['current_model'], inline=True)
        embed.add_field(name="AI Image Service Status", value=status_report_data['image_service_status'], inline=True)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=f"AI-Chat V{status_report_data['version']}")
        await interaction.followup.send(embed = embed)
        log("info", "proc.status", "Status report sent.")
    else:
        return

#Command: Debug Logging
@tree.command(
        name="debuglog",
        description="Turns debug logging on / off."
)
async def debug_log(interaction: discord.Interaction, option:Literal["on", "off"]):
    if bot_online == True:
        await interaction.response.defer()
        log("info", "proc.debglog", "Debug logging option command recieved.")
        if option == "on":
            log("info", "proc.debglog", "Turning debug logging on.")
            result = requests.post(url_bot_debug_log, headers=headers, json={'option': 'on'})
            if result.status_code == 200:
                log("info", "proc.debglog", "Debug logging mode turned on.")
                await interaction.followup.send(content = "Debug logging mode turned on.")
            else:
                log("warning", "proc.debglog", f"Request failed. Status code: {result.status_code}.")
                await interaction.followup.send(content=f"Request failed. Status code: {result.status_code}.")
        else:
            log("info", "proc.debglog", "Turning debug logging off.")
            result = requests.post(url_bot_debug_log, headers=headers, json={'option': 'off'})
            if result.status_code == 200:
                log("info", "proc.debglog", "Debug logging mode turned off.")
                await interaction.followup.send(content="Debug logging mode turned off.")
            else:
                log("warning", "proc.debglog", f"Request failed. Status code: {result.status_code}.")
                await interaction.followup.send(content=f"Request failed. Status code: {result.status_code}.")
    else:
        return
            
#Command: Image Generation Rank
@tree.command(
    name="imagegenrank",
    description="Shows the rank of different user's image generation times.",
)
async def image_generation_rank(interaction: discord.Interaction):
    if bot_online == True:
        log("info", "proc.imgrank", "Image generation rank command received.")
        await interaction.response.defer()
        log("debug", "proc.imgrank", "Sending request to get image generation rank.")
        rank = requests.get(url_bot_image_rank, headers=headers, verify=False).json()['rank']
        log("info", "proc.imgrank", "Image generation rank received. Sending rank.")
        
        # Sort the rank dictionary by value in descending order
        rank_sorted = sorted(rank.items(), key=lambda item: item[1], reverse=True)
        
        # Format the sorted rank dictionary into a string
        rank_str = "\n".join([f"{i+1}. {user}: {score}" for i, (user, score) in enumerate(rank_sorted)])
        embed = discord.Embed(title="Image Generation Rank", color=int('FE9900', 16))
        embed.add_field(name="Rank", value=rank_str, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed = embed)
    else:
        return

#Command: Announce Message
@tree.command(
    name="announce",
    description="Announces a message to a channel.",
)
async def announce_message(interaction: discord.Interaction, channel: Literal["update-news", "update-news-test"], message: str):
    if bot_online == True:
        log("info", "proc.annomsg", "Announce message command received.")
        await interaction.response.defer()
        message = message.replace("\\n", "\n")
        if interaction.user.name == "jimmyn3577":
            log("info", "proc.annomsg", "User authorized. Announcing message...")
            if channel == "update-news":
                log("info", "proc.annomsg", "Announcing message to update-news channel.")
                await client.get_channel(1216287821950746624).send(f"{message}")
                await interaction.followup.send(content = "Message announced.")
            elif channel == "update-news-test":
                log("info", "proc.annomsg", "Announcing message to update-news-test channel.")
                await client.get_channel(1217622465727959130).send(f"{message}")
                await interaction.followup.send(content = "Message announced.")
        else:
            log("warning", "proc.annomsg", "User not authorized. Rejecting request.")
            await interaction.followup.send("You do not have permission to announce a message.")
    else:
        return

#Command: Pause Bot
@tree.command(
    name="pausebot",
    description="Pauses the bot.",
)
async def pause_bot(interaction: discord.Interaction, option:Literal["pause", "resume"]):
    global bot_online
    log("info", "proc.botstop", "Pause bot command received.")
    await interaction.response.defer()
    if interaction.user.name == "jimmyn3577":
        if option == "pause":
            log("info", "proc.botstop", "User authorized. Stopping bot...")
            await interaction.followup.send("Pausing bot...")
            try:
                log("debug", "proc.botstop", "Sending request to stop bot.")
                bot_online = False
                requests.post(url_bot_pause, headers=headers, verify=False, json={"mode": "pause"})
            except Exception:
                log("warning", "proc.botstop", "Failed to pause bot.")
                await interaction.followup.send("Failed to pause bot.")
        if option == "resume":
            log("info", "proc.botstop", "User authorized. Stopping bot...")
            await interaction.followup.send("Resuming bot...")
            try:
                log("debug", "proc.botstop", "Sending request to stop bot.")
                bot_online = True
                requests.post(url_bot_pause, headers=headers, verify=False, json={"mode": "resume"})
            except Exception:
                log("warning", "proc.botstop", "Failed to resume bot.")
                await interaction.followup.send("Failed to resume bot.")
    else:
        log("warning", "proc.botstop", "User not authorized. Rejecting request.")
        await interaction.followup.send("You do not have permission to stop the bot.")

#Command: Personality AI Mode
@tree.command(
    name="personality",
    description="Adjusts the personality AI mode.",
)
async def personality(interaction: discord.Interaction, option:Literal["Normal", "Gemini"]):
    await interaction.response.defer()
    log("info", "proc.peropts", "Personality AI mode command received.")
    log("info", "proc.peropts", f"Personality AI mode selected: {option}. Sending request...")
    requests.post(url_bot_personality_mode, headers=headers, json={"mode": option}, verify=False)
    log("info", "proc.peropts", "Personality AI mode updated.")
    await interaction.followup.send(content = f"Personality AI mode updated to {option}.")

@client.event
async def on_ready():
    await tree.sync()
    log("info", "main.startup", "Command tree synced. Ready to accept commands.")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client.run(token)