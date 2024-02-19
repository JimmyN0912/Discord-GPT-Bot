import os
import sys
import time

time.sleep(1)  # wait for bot to close
os.system("git pull")
os.system("start cmd /k python GPT-Bot.py")
os.system("start cmd /k python slash-commands.py")