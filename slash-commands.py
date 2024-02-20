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
def log(lvl, service, log_msg):
    logger.log(f"{lvl}  {service}    {log_msg}")

#Logging service names
    #main.startup
    #proc.getlogs
    #proc.clrchan
    #proc.mdlopts
    #proc.botstop
    #proc.botupda
    #proc.botrest

### Global Variables ###
headers = {"Content-Type": "application/json"}
url_bot_service_mode = "http://localhost:5000/api/service_mode"
url_bot_current_model_ngc = "http://localhost:5000/api/ngc/current_model"
url_bot_ngc_models = "http://localhost:5000/api/ngc/models"
url_bot_ngc_load_model = "http://localhost:5000/api/ngc/load_model"
url_bot_stop = "http://localhost:5000/stop"
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

#Command: Get Logs
@tree.command(
    name="getlogs",
    description="Sends the log file of the script.",
)
async def get_logs(interaction: discord.Interaction):
    log("INFO", "proc.getlogs", "Get logs command received. Loading logs...")
    await interaction.response.send_message(file=discord.File("C:\GPT-Bot\logs\GPT-Bot.log"))
    log("INFO", "proc.getlogs", "Log file sent.")

#Command: Clear Channel
@tree.command(
    name="clearchannel",
    description="Clears the channel.",
)
async def clear_channel(interaction: discord.Interaction):
    log("INFO", "proc.clrchan", "Clear channel command received. Clearing channel...")
    await interaction.response.send_message("Clearing channel...")
    await interaction.channel.purge()
    log("INFO", "proc.clrchan", "Channel cleared.")

#Command: Model Options
@tree.command(
    name="model",
    description="Options: info, load, unload, reload",
)
async def model_options(interaction: discord.Interaction, option: Literal["info", "load", "unload"], model_name: Optional[str] = None):
    log("INFO", "proc.mdlopts", "Model option command received.")
    await interaction.response.defer()
    if option == "info":
        log("DEBG", "proc.mdlopts", "Model info requested.")
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        log("INFO", "proc.mdlopts", f"Bot service mode: {service_mode}.")
        if service_mode == "Local":
            log("DEBG", "proc.mdlopts", "Querying current loaded model.")
            current_model = requests.get(url_server_model_info, headers=headers, verify=False).json()['model_name']
            log("DEBG", "proc.mdlopts", "Querying available models.")
            model_names = requests.get(url_server_list_model, headers=headers, verify=False).json()['model_names']
            model_list = "\n".join(f"{i}. {model}" for i, model in enumerate(model_names,1))
            log("INFO", "proc.mdlopts", "Processing complete. Sending model info.")
            await interaction.followup.send(content = f"Current Model Server: {service_mode}\n\nCurrent Model: {current_model}\n\nAvailable Models:\n{model_list}")
        else:
            log("DEBG", "proc.mdlopts", "Querying current loaded model.")
            current_model = requests.get(url_bot_current_model_ngc, headers=headers, verify=False).json()['current_model']
            log("DEBG", "proc.mdlopts", "Querying available models.")
            model_names = requests.get(url_bot_ngc_models, headers=headers, verify=False).json()['ngc_models']
            model_list = "\n".join(f"{i}. {model}" for i, model in enumerate(model_names,1))
            log("INFO", "proc.mdlopts", "Processing complete. Sending model info.")
            await interaction.followup.send(content = f"Current Model Server: {service_mode}\n\nCurrent Model: {current_model}\n\nAvailable Models:\n{model_list}")
    elif option == "load":
        log("DEBG", "proc.mdlopts", f"Model load requested. Model selected: {model_name}.")
        if model_name is None:
            log("WARN", "proc.mdlopts", "Model name not specified. Rejecting request.")
            await interaction.response.send_message("Please specify a model name.")
            return
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        log("INFO", "proc.mdlopts", f"Bot service mode: {service_mode}.")
        if service_mode == "Local":
            log("DEBG", "proc.mdlopts", "Querying current loaded model.")
            current_model = requests.get(url_server_model_info, headers=headers, verify=False).json()['model_name']
            if model_name == current_model:
                log("WARN", "proc.mdlopts", "Model is already loaded. Rejecting request.")
                await interaction.followup.send(content = f"Model {model_name} is already loaded.")
                return
            message = await interaction.followup.send(content = f"Loading Model: {model_name}")
            payload = {"model_name": model_name, "args": load_model_args[model_name]}
            log("DEBG", "proc.mdlopts", "Sending request to load model.")
            response = requests.post(url_server_load_model, json=payload, headers=headers, verify=False)
            if response.status_code == 200:
                log("INFO", "proc.mdlopts", f"Model {model_name} loaded.")
                await message.edit(content = f"Model Loaded: {model_name}")
            else:
                log("WARN", "proc.mdlopts", f"Failed to load model: {model_name}.")
                await message.edit(content = f"Failed to load model: {model_name}")
        else:
            log("DEBG", "proc.mdlopts", "Querying current loaded model.")
            current_model = requests.get(url_bot_current_model_ngc, headers=headers, verify=False).json()['current_model']
            if model_name == current_model:
                log("WARN", "proc.mdlopts", "Model is already loaded. Rejecting request.")
                await interaction.followup.send(content = f"Model {model_name} is already loaded.")
                return
            message = await interaction.followup.send(content = f"Loading Model: {model_name}")
            payload = {"model_name": model_name}
            log("DEBG", "proc.mdlopts", "Sending request to load model.")
            response = requests.post(url_bot_ngc_load_model, json=payload, headers=headers, verify=False)
            if response.status_code == 200:
                log("INFO", "proc.mdlopts", f"Model {model_name} loaded.")
                await message.edit(content = f"Model Loaded: {model_name}")
            else:
                log("WARN", "proc.mdlopts", f"Failed to load model: {model_name}.")
                await message.edit(content = f"Failed to load model: {model_name}")
    elif option == "unload":
        log("DEBG", "proc.mdlopts", "Model unload requested.")
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        log("INFO", "proc.mdlopts", f"Bot service mode: {service_mode}.")
        if service_mode == "NGC":
            log("WARN", "proc.mdlopts", "Unload Model: Not Supported for NGC. Rejecting request.")
            await interaction.followup.send(content = "Unload Model: Not Supported for NGC")
            return
        log("DEBG", "proc.mdlopts", "Sending request to unload model.")
        response = requests.post(url_server_unload_model, headers=headers, verify=False)
        if response.status_code == 200:
            log("INFO", "proc.mdlopts", "Model Unloaded.")
            await interaction.followup.send(content = "Model Unloaded")
        else:
            log("WARN", "proc.mdlopts", "Failed to unload model.")
            await interaction.followup.send(content = "Failed to unload model")

#Command: Stop Bot
@tree.command(
    name="stopbot",
    description="Stops the bot.",
)
async def stop_bot(interaction: discord.Interaction):
    log("INFO", "proc.botstop", "Stop bot command received.")
    if interaction.user.name == "jimmyn3577":
        log("INFO", "proc.botstop", "User authorized. Stopping bot...")
        await interaction.response.send_message("Stopping bot...")
        try:
            log("DEBG", "proc.botstop", "Sending request to stop bot.")
            requests.post(url_bot_stop, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            pass
        log("DEBG", "proc.botstop", "Stopping command processer.")
        await client.close()
    else:
        log("WARN", "proc.botstop", "User not authorized. Rejecting request.")
        await interaction.response.send_message("You do not have permission to stop the bot.")

#Command: Update Bot
@tree.command(
    name="updatebot",
    description="Updates the bot.",
)
async def update_bot(interaction: discord.Interaction):
    log("INFO", "proc.botupda", "Update bot command received.")
    if interaction.user.name == "jimmyn3577":
        log("INFO", "proc.botupda", "User authorized. Updating bot...")
        await interaction.response.send_message("Updating bot...")
        try:
            log("DEBG", "proc.botupda", "Sending request to stop bot.")
            requests.post(url_bot_stop, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            pass
        log("DEBG", "proc.botupda", "Starting update process.")
        subprocess.Popen(["python", "update.py"])
        log("DEBG", "proc.botupda", "Update complete. Restarting...")
        await client.close()
    else:
        log("WARN", "proc.botupda", "User not authorized. Rejecting request.")
        await interaction.response.send_message("You do not have permission to update the bot.")

#Command: Restart Bot
@tree.command(
    name="restartbot",
    description="Restarts the bot.",
)
async def restart_bot(interaction: discord.Interaction):
    log("INFO", "proc.botrest", "Restart bot command received.")
    if interaction.user.name == "jimmyn3577":
        log("INFO", "proc.botrest", "User authorized. Restarting bot...")
        await interaction.response.send_message("Restarting bot...")
        try:
            log("DEBG", "proc.botrest", "Sending request to stop bot.")
            requests.post(url_bot_stop, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            pass
        log("DEBG", "proc.botrest", "Starting restart process.")
        subprocess.Popen(["python", "restart.py"])
        await client.close()
    else:
        log("WARN", "proc.botrest", "User not authorized. Rejecting request.")
        await interaction.response.send_message("You do not have permission to restart the bot.")

@client.event
async def on_ready():
    await tree.sync()
    log("INFO", "main.startup", "Command tree synced. Ready to accept commands.")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client.run(token)