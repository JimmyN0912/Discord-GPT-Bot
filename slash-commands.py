import discord
import os
from dotenv import load_dotenv
from typing import Literal, Optional
import requests
from collections import defaultdict
import subprocess

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

#Global Variables
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

#Command: Get Logs
@tree.command(
    name="getlogs",
    description="Sends the log file of the script.",
)
async def get_logs(interaction: discord.Interaction):
    await interaction.response.send_message(file=discord.File("C:\GPT-Bot\logs\GPT-Bot.log"))

#Command: Clear Channel
@tree.command(
    name="clearchannel",
    description="Clears the channel.",
)
async def clear_channel(interaction: discord.Interaction):
    await interaction.response.send_message("Clearing channel...")
    await interaction.channel.purge()

#Command: Model Options
@tree.command(
    name="model",
    description="Options: info, load, unload, reload",
)
async def model_options(interaction: discord.Interaction, option: Literal["info", "load", "unload"], model_name: Optional[str] = None):
    await interaction.response.defer()
    if option == "info":
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        if service_mode == "Local":
            current_model = requests.get(url_server_model_info, headers=headers, verify=False).json()['model_name']
            model_names = requests.get(url_server_list_model, headers=headers, verify=False).json()['model_names']
            model_list = "\n".join(f"{i}. {model}" for i, model in enumerate(model_names,1))
            await interaction.followup.send(content = f"Current Model Server: {service_mode}\n\nCurrent Model: {current_model}\n\nAvailable Models:\n{model_list}")
        else:
            current_model = requests.get(url_bot_current_model_ngc, headers=headers, verify=False).json()['current_model']
            model_names = requests.get(url_bot_ngc_models, headers=headers, verify=False).json()['ngc_models']
            model_list = "\n".join(f"{i}. {model}" for i, model in enumerate(model_names,1))
            await interaction.followup.send(content = f"Current Model Server: {service_mode}\n\nCurrent Model: {current_model}\n\nAvailable Models:\n{model_list}")
    elif option == "load":
        if model_name is None:
            await interaction.response.send_message("Please specify a model name.")
            return
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        if service_mode == "Local":
            current_model = requests.get(url_server_model_info, headers=headers, verify=False).json()['model_name']
            if model_name == current_model:
                await interaction.followup.send(content = f"Model {model_name} is already loaded.")
                return
            message = await interaction.followup.send(content = f"Loading Model: {model_name}")
            payload = {"model_name": model_name, "args": load_model_args[model_name]}
            response = requests.post(url_server_load_model, json=payload, headers=headers, verify=False)
            if response.status_code == 200:
                await message.edit(content = f"Model Loaded: {model_name}")
            else:
                await message.edit(content = f"Failed to load model: {model_name}")
        else:
            current_model = requests.get(url_bot_current_model_ngc, headers=headers, verify=False).json()['current_model']
            if model_name == current_model:
                await interaction.followup.send(content = f"Model {model_name} is already loaded.")
                return
            message = await interaction.followup.send(content = f"Loading Model: {model_name}")
            payload = {"model_name": model_name}
            response = requests.post(url_bot_ngc_load_model, json=payload, headers=headers, verify=False)
            if response.status_code == 200:
                await message.edit(content = f"Model Loaded: {model_name}")
            else:
                await message.edit(content = f"Failed to load model: {model_name}")
    elif option == "unload":
        service_mode = requests.get(url_bot_service_mode, headers=headers, verify=False).json()['service_mode']
        if service_mode == "NGC":
            await interaction.followup.send(content = "Unload Model: Not Supported for NGC")
            return
        response = requests.post(url_server_unload_model, headers=headers, verify=False)
        if response.status_code == 200:
            await interaction.followup.send(content = "Model Unloaded")
        else:
            await interaction.followup.send(content = "Failed to unload model")

#Command: Stop Bot
@tree.command(
    name="stopbot",
    description="Stops the bot.",
)
async def stop_bot(interaction: discord.Interaction):
    if interaction.user.name == "jimmyn3577":
        await interaction.response.send_message("Stopping bot...")
        try:
            stop_bot = requests.post(url_bot_stop, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            pass
        await client.close()
    else:
        await interaction.response.send_message("You do not have permission to stop the bot.")

#Command: Update Bot
@tree.command(
    name="updatebot",
    description="Updates the bot.",
)
async def update_bot(interaction: discord.Interaction):
    if interaction.user.name == "jimmyn3577":
        await interaction.response.send_message("Updating bot...")
        try:
            stop_bot = requests.post(url_bot_stop, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            pass
        subprocess.Popen(["python", "update.py"])
        await client.close()
    else:
        await interaction.response.send_message("You do not have permission to update the bot.")

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client.run(token)