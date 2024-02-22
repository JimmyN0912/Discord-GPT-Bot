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

### Global Variables ###
headers = {"Content-Type": "application/json"}
url_bot_service_mode = "http://localhost:5000/api/service_mode"
url_bot_current_model_ngc = "http://localhost:5000/api/ngc/current_model"
url_bot_ngc_models = "http://localhost:5000/api/ngc/models"
url_bot_ngc_load_model = "http://localhost:5000/api/ngc/load_model"
url_bot_clear_context = "http://localhost:5000/api/clear_context"
url_bot_context_export = "http://localhost:5000/api/context_export"
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
# 7. Clear Context
# 8. Context Export

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
            requests.post(url_bot_stop, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            pass
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
    log("info", "proc.ctxexp", "Context export command received.")
    message = await interaction.followup.send(content = "Exporting context...")
    request_result = requests.post(url_bot_context_export, headers=headers, json={"user_id" : interaction.user.id}, verify=False).json()
    if request_result["status"] == "no_export":
        log("warning", "proc.ctxexp", "Context not modified. No context to export.")
        await message.edit(content = "Context not modified. No context to export.")
    else:
        log("info", "proc.ctxexp", "Context exported. Sending file...")
        await message.edit(content = "Context exported:")
        await interaction.channel.send(file = discord.File(request_result["file_name"]))
    


@client.event
async def on_ready():
    await tree.sync()
    log("info", "main.startup", "Command tree synced. Ready to accept commands.")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client.run(token)