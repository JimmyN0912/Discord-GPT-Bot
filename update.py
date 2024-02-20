import os
import time

time.sleep(1)  # wait for bot to close
os.system("git pull")
os.system("powershell -Command {python GPT-Bot.py; pause}")
os.system("powershell -Command {python slash-commands.py; pause}")