import os
import time
import subprocess

time.sleep(1)  # wait for bot to close
os.system("git pull")
subprocess.Popen('powershell Start-Process python -ArgumentList "GPT-Bot.py"')
subprocess.Popen('powershell Start-Process python -ArgumentList "slash-commands.py"')