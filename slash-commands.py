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

### Global Variables ###
headers = {"Content-Type": "application/json"}
url_bot_service_mode = "http://localhost:5000/api/service_mode"
url_bot_current_model_ngc = "http://localhost:5000/api/ngc/current_model"
url_bot_ngc_models = "http://localhost:5000/api/ngc/models"
url_bot_ngc_load_model = "http://localhost:5000/api/ngc/load_model"
url_bot_clear_context = "http://localhost:5000/api/clear_context"
url_bot_context_export = "http://localhost:5000/api/context_export"
url_bot_status = "http://localhost:5000/api/status"
url_bot_debug_log = "http://localhost:5000/api/debug_log"
url_bot_service_update = "http://localhost:5000/api/service_update"
url_bot_image_rank = "http://localhost:5000/api/imagegen_rank"
url_bot_stop = "http://localhost:5000/stop"
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
# 11.Service Check
# 12.Image Generation Rank

#Command: Get Logs
@tree.command(
    name="getlogs",
    description="Sends the log file of the script.",
)
async def get_logs(interaction: discord.Interaction):
    log("info", "proc.getlogs", "Get logs command received. Loading logs...")
    await interaction.response.send_message(file=discord.File("C:\GPT-Bot\logs\GPT-Bot.log"))
    log("info", "proc.getlogs", "Log file sent.")

#Command: Clear Channel
@tree.command(
    name="clearchannel",
    description="Clears the channel.",
)
async def clear_channel(interaction: discord.Interaction):
    log("info", "proc.clrchan", "Clear channel command received. Clearing channel...")
    await interaction.response.send_message("Clearing channel...")
    await interaction.channel.purge()
    log("info", "proc.clrchan", "Channel cleared.")

#Command: Model Options
@tree.command(
    name="model",
    description="Options: info, load, unload, reload",
)
async def model_options(interaction: discord.Interaction, option: Literal["info", "load", "unload"], model_name: Optional[str] = None):
    log("info", "proc.mdlopts", "Model option command received.")
    await interaction.response.defer()
    if option == "info":
        log("debug", "proc.mdlopts", "Model info requested.")
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        log("info", "proc.mdlopts", f"Bot service mode: {service_mode}.")
        if service_mode == "Local":
            log("debug", "proc.mdlopts", "Querying current loaded model.")
            current_model = requests.get(url_server_model_info, headers=headers, verify=False).json()['model_name']
            log("debug", "proc.mdlopts", "Querying available models.")
            model_names = requests.get(url_server_list_model, headers=headers, verify=False).json()['model_names']
            model_list = "\n".join(f"{i}. {model}" for i, model in enumerate(model_names,1))
            log("info", "proc.mdlopts", "Processing complete. Sending model info.")
            await interaction.followup.send(content = f"Current Model Server: {service_mode}\n\nCurrent Model: {current_model}\n\nAvailable Models:\n{model_list}")
        else:
            log("debug", "proc.mdlopts", "Querying current loaded model.")
            current_model = requests.get(url_bot_current_model_ngc, headers=headers, verify=False).json()['current_model']
            log("debug", "proc.mdlopts", "Querying available models.")
            model_names = requests.get(url_bot_ngc_models, headers=headers, verify=False).json()['ngc_models']
            model_list = "\n".join(f"{i}. {model}" for i, model in enumerate(model_names,1))
            log("info", "proc.mdlopts", "Processing complete. Sending model info.")
            await interaction.followup.send(content = f"Current Model Server: {service_mode}\n\nCurrent Model: {current_model}\n\nAvailable Models:\n{model_list}")
    elif option == "load":
        log("debug", "proc.mdlopts", f"Model load requested. Model selected: {model_name}.")
        if model_name is None:
            log("warning", "proc.mdlopts", "Model name not specified. Rejecting request.")
            await interaction.response.send_message("Please specify a model name.")
            return
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        log("info", "proc.mdlopts", f"Bot service mode: {service_mode}.")
        if service_mode == "Local":
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
            log("debug", "proc.mdlopts", "Querying current loaded model.")
            current_model = requests.get(url_bot_current_model_ngc, headers=headers, verify=False).json()['current_model']
            if model_name == current_model:
                log("warning", "proc.mdlopts", "Model is already loaded. Rejecting request.")
                await interaction.followup.send(content = f"Model {model_name} is already loaded.")
                return
            message = await interaction.followup.send(content = f"Loading Model: {model_name}")
            payload = {"model_name": model_name}
            log("debug", "proc.mdlopts", "Sending request to load model.")
            response = requests.post(url_bot_ngc_load_model, json=payload, headers=headers, verify=False)
            if response.status_code == 200:
                log("info", "proc.mdlopts", f"Model {model_name} loaded.")
                await message.edit(content = f"Model Loaded: {model_name}")
            else:
                log("warning", "proc.mdlopts", f"Failed to load model: {model_name}.")
                await message.edit(content = f"Failed to load model: {model_name}")
    elif option == "unload":
        log("debug", "proc.mdlopts", "Model unload requested.")
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        log("info", "proc.mdlopts", f"Bot service mode: {service_mode}.")
        if service_mode == "NGC":
            log("warning", "proc.mdlopts", "Unload Model: Not Supported for NGC. Rejecting request.")
            await interaction.followup.send(content = "Unload Model: Not Supported for NGC")
            return
        log("debug", "proc.mdlopts", "Sending request to unload model.")
        response = requests.post(url_server_unload_model, headers=headers, verify=False)
        if response.status_code == 200:
            log("info", "proc.mdlopts", "Model Unloaded.")
            await interaction.followup.send(content = "Model Unloaded")
        else:
            log("warning", "proc.mdlopts", "Failed to unload model.")
            await interaction.followup.send(content = "Failed to unload model")

#Command: Stop Bot
@tree.command(
    name="stopbot",
    description="Stops the bot.",
)
async def stop_bot(interaction: discord.Interaction):
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

#Command: Update Bot
@tree.command(
    name="updatebot",
    description="Updates the bot.",
)
async def update_bot(interaction: discord.Interaction):
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

#Command: Restart Bot
@tree.command(
    name="restartbot",
    description="Restarts the bot.",
)
async def restart_bot(interaction: discord.Interaction):
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

#Command: Clear Context
@tree.command(
    name="clearcontext",
    description="Clears the context history.",
)
async def clear_context(interaction: discord.Interaction):
    await interaction.response.defer()
    log("info", "proc.clrcont", "Clear context command received.")
    message = await interaction.followup.send(content = "Clearing context...")
    requests.post(url_bot_clear_context, headers=headers, json={"user_id" : interaction.user.id}, verify=False)
    await message.edit(content = "Context cleared.")

#Command: Context Export
@tree.command(
    name="contextexport",
    description="Exports the context history.",
)
async def context_export(interaction: discord.Interaction):
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
    
#Command: Status
@tree.command(
    name="status",
    description="Displays the status of the bot.",
)
async def status(interaction: discord.Interaction):
    await interaction.response.defer()
    log("info", "proc.status", "Status command received.")
    status_report_data = requests.get(url_bot_status, headers=headers, verify=False).json()
    total_responses = status_report_data["local_responses"] + status_report_data["ngc_responses"]
    status_report = f"AI-Chat V{status_report_data['version']}\nVersion date:{status_report_data['version_date']}\n\nStatus:\n1. Bot uptime: {status_report_data['uptime']} {status_report_data['uptime_unit']}\n2. Total text responses: {total_responses}\n3. Local text responses: {status_report_data['local_responses']}\n4. NGC text responses: {status_report_data['ngc_responses']}\n5. NGC image responses: {status_report_data['ngc_image_responses']}\n6. Debug logging: {status_report_data['logging_mode']}\n7. AI text service mode: {status_report_data['text_service_mode']}\n8. Current local AI Model: {status_report_data['current_model']}\n9. Current NGC AI Model: {status_report_data['current_model_ngc']}\n10. AI image service mode: {status_report_data['image_service_mode']}"
    log("info", "proc.status", "Sending status report.")
    await interaction.followup.send(content = status_report)

#Command: Debug Logging
@tree.command(
        name="debuglog",
        description="Turns debug logging on / off."
)
async def debug_log(interaction: discord.Interaction, option:Literal["on", "off"]):
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

#Command: Service Check
@tree.command(
    name="servicecheck",
    description="Checks the status of the bot services.",
)
async def service_check(interaction: discord.Interaction):
    await interaction.response.defer()
    log("info", "proc.chcksvc", "Service check command received.")
    try:
        log("debug", "proc.chcksvc", "Testing local AI text service.")
        test = requests.get(url_server_test, timeout=3, headers=headers, verify=False)
        if test.status_code == 200:
            log("info", "proc.chcksvc", "Local AI service online. Selecting as default.")
            update = requests.post(url_bot_service_update, headers=headers, json={"service": "text","mode": "local"}, verify=False)
            if update.status_code == 200:
                log("info", "proc.chcksvc", "Local AI service selected as default.")
                await interaction.followup.send(content = "Local AI service online. Selected as default.")
            else:
                log("warning", "proc.chcksvc", "Failed to select local AI service as default.")
                await interaction.followup.send(content = "Local AI service online. Failed to select as default.")
    except requests.exceptions.ConnectionError:
        log("warning", "proc.chcksvc", "Local AI service offline.")
        log("info", "proc.chcksvc", "Local AI service offline. Selecting NGC as default.")
        await interaction.followup.send(content = "Local AI service offline. Selecting NGC as default.")
        update = requests.post(url_bot_service_update, headers=headers, json={"service": "text","mode": "ngc"}, verify=False)
        if update.status_code == 200:
            log("info", "proc.chcksvc", "NGC AI service selected as default.")
            await interaction.followup.send(content = "NGC AI service selected as default.")
        else:
            log("warning", "proc.chcksvc", "Failed to select NGC AI service as default.")
            await interaction.followup.send(content = "NGC AI service offline. Failed to select as default.")

    try:
        log("info", "proc.chcksvc", "Testing local AI image service.")
        test = requests.get(url_image_server_test, timeout=3, headers=headers, verify=False)
        if test.status_code == 200:
            log("info", "proc.chcksvc", "Local AI image service online. Selecting as default.")
            update = requests.post(url_bot_service_update, headers=headers, json={"service": "image","mode": "local"}, verify=False)
            if update.status_code == 200:
                log("info", "proc.chcksvc", "Local AI image service selected as default.")
                await interaction.followup.send(content = "Local AI image service online. Selected as default.")
            else:
                log("warning", "proc.chcksvc", "Failed to select local AI image service as default.")
                await interaction.followup.send(content = "Local AI image service online. Failed to select as default.")
    except requests.exceptions.ConnectionError:
        log("warning", "proc.chcksvc", "Local AI image service offline.")
        log("info", "proc.chcksvc", "Local AI image service offline. Selecting NGC as default.")
        await interaction.followup.send(content = "Local AI image service offline. Selecting NGC as default.")
        update = requests.post(url_bot_service_update, headers=headers, json={"service": "image","mode": "ngc"}, verify=False)
        if update.status_code == 200:
            log("info", "proc.chcksvc", "NGC AI image service selected as default.")
            await interaction.followup.send(content = "NGC AI image service selected as default.")
        else:
            log("warning", "proc.chcksvc", "Failed to select NGC AI image service as default.")
            await interaction.followup.send(content = "NGC AI image service offline. Failed to select as default.")
            
#Command: Image Generation Rank
@tree.command(
    name="imagegenrank",
    description="Shows the rank of different user's image generation times.",
)
async def image_generation_rank(interaction: discord.Interaction):
    log("info", "proc.imgrank", "Image generation rank command received.")
    await interaction.response.defer()
    log("debug", "proc.imgrank", "Sending request to get image generation rank.")
    rank = requests.get(url_bot_image_rank, headers=headers, verify=False).json()['rank']
    log("info", "proc.imgrank", "Image generation rank received. Sending rank.")
    
    # Sort the rank dictionary by value in descending order
    rank_sorted = sorted(rank.items(), key=lambda item: item[1], reverse=True)
    
    # Format the sorted rank dictionary into a string
    rank_str = "\n".join([f"{i+1}. {user}: {score}" for i, (user, score) in enumerate(rank_sorted)])
    
    await interaction.followup.send(content = f"Image Generation Rank:\n{rank_str}")

@client.event
async def on_ready():
    await tree.sync()
    log("info", "main.startup", "Command tree synced. Ready to accept commands.")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client.run(token)