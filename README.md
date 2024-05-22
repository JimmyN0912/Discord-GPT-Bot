# Discord GPT Bot

This repository contains the code for a Discord AI Chatbot Bot. The bot consists of several Python files, each serving a specific purpose.

## Features
The Discord AI Chatbot has the folowing features:

- ### **Text Generation**: 

    The bot can generates AI text response when the user mentions the bot. There are two modes for text generation.
    > Message example: `@AI-Chat` who are you?
    
    - Normal mode:

        When the message is in `Text-To-Text` channel category, the bot generates AI response via local [text-generation-webui](https://github.com/oobabooga/text-generation-webui) instance on separate laptop.

        Supported Models:
        | Model Name | Vendor/Creater | Parameter Size | Quantisation |
        |------------|----------------|----------------|--------------|
        |   Llama-2  |      Meta      |       7B       |    Q4_K_M    |
        |   Llama-2  |      Meta      |       13B      |    Q4_K_M    |
        | Mistral-7B |   Mistral-AI   |       7B       |    Q4_K_M    |
        |   Llama-3  |      Meta      |       8B       |    Q4_K_M    |
        |   Llama-3  |      Meta      |       70B      |    Q4_K_M    |
        |  TAIDE-LX  |     TAIDE      |       7B       |  Unquantised |
        |Zephyr-Beta |   HuggingFace  |   7B(Q4_K_M)   |    Q4_K_M    |
        > These models are all optained from [HuggingFace](https://huggingface.co/), more model options may come in the future.

        > Main model used is currently **Llama-3-8B**

    - Google Gemini mode:

        When the message is in `Google-Gemini` channel category, the bot generates AI response via Google Gemini API. If the user sends a picture alongside a text message, Google Gemini is capable of using what it saw on the picture to respond.
        > Image mode is only possible in single-turn conversations, which is the `#normal` channel. Image mode currently doesn't multi-turn conversations. This is a limitation of the Gemini model, not the Discord chatbot.

        Supported Models:
        1. **Gemini 1.0 Pro**: This is the model used in normal multi-turn conversations.
        2. **Gemini Pro Vision**: This is the model used when the user sends a picture alongside text message, and the AI model is capable of respond based on the picture to some extend.

    - Personality Modes:

        Just like ChatGPT's GPT Store, Personality mode contains assistants that have different system prompts, for different use cases. More personalities may come in the future!

        Personalities:
        1. **Text-Adventure**: Under this mode, the assistant will generate a scenario and some actions for the user, where the user can choose an option, and start a text adventure with the bot.
        2. **Story-Writer**: Here the user can write a story with the assistant. When the user sends a message about the beginning of the story, the bot will return with a story written from the prompt. The user can then continue with the story or tweak the story with further messages.

    ---

- ### **Image Generation**:
    The bot can generate a picture based on the user's input prompt.
    > Prompt example: `@AI-Chat` A picture of a futuristic sedan.

    The channel category for image generation is `Text-To-Image`, and the bot will respond with an embed message.

    The embed message contains:

    1. The prompt used to generate the image, which is the user's input prompt.
    2. Total images generation count by the user.  
    3. AI model used to generate the image, currently it's **Fluently-V1**, new model may come in the future.
    4. The version of AI-Chat.
    5. The time when the image is generated.

    Model used:

    - Fluently-V1

    ---

- ### **Music Generation**
    The bot can generate a 6 second music clip from the user's input prompt.
    > Prompt example: `@AI-Chat` A calm lofi hip-hop msuic.

    Model Used:

    - Musicgen-stereo-Medium by Facebook(Meta)

    ---

- ### **Video Generation**:
    The bot can generate a GIF video from the user's input prompt.
    > Prompt example: `@AI-Chat` A car driving down a highway.

    Model Used:

    - AnimateDiff-Lightning by ByteDance


## Files

### GPT-Bot.py

The `GPT-Bot.py` file contains the main logic for the Discord GPT Bot. It handles the bot's interactions with the Discord API, including message handling and response generation.

### restart.py

The `restart.py` file contains the code required for the bot to restart itself (`GPT-Bot.py` and `slash-commands.py`) on slash command request.

### update.py

The `update.py` file contains the code for the bot to stop all it's processes (`GPT-Bot.py` and `slash-commands.py`), perform a `git pull`, and then restart all services on slash command request.

### slash-commands.py

The `slash-commands.py` file implements the slash commands functionality for the Discord GPT Bot. It defines the available slash commands and their corresponding actions.

### inference-server.py

The `inference-server.py` file sets up an inference server for the model used by the bot. It currently handles music and video generations, other generations endpoints (text, image) will be merged here in the future.

### streamlit_voice_chat.py

The `streamlit_voice_chat.py` file implements a Streamlit app for voice chat functionality. It accepts user voice recording as input, and generates speech as the response. Since Discord in Python doesn't support voice chat functionality, this will be the way I implement a voice assistant.

## Updates

### Overview
|      Component     |Version|
|--------------------|-------|
|      GPT-Bot       | V21.1 |
|Streamlit Voice Chat| V2.0  |

<details>
<summary>Changelog for GPT-Bot</summary>

#### Version 2.0: 2023/12/08
- Added logging to file ability by Python logging library
- Completely rewritten logging processes
- Separated status report info a standalone method
- Removed unused OpenAI info

---

#### Version 2.1: 2023/12/08
- Separated AI requesting to "ai_request" method
- Separated AI response parsing to "ai_response" method

---

#### Version 2.2: 2023/12/08
- Removed some unused process names
- Fixed a bug where only INFO level logs are being logged
- Corrected reply.status logging (message.proc->reply.status)
- Added a feature for the bot to have different presence when doing different tasks
- Moved logs to "logs" folder
- Removed old logs

Bot Presences:
- Normal: Playing the waiting game.
- Status Report: Streaming status report. (url is set to https://www.huggingface.co for now, may change in the future)
- Requesting AI: Streaming AI data.

---

#### Version 2.3: 2023/12/10
- Troubleshooting LLaMa server generation error
- Modified AI prompt
- Added command to send logs to Discord chat

Note: LLaMa server usage will be deprecated next release, will switch to text-generation-webui api instead.

---

#### Version 3.0: 2023/12/10
- Successfully switched to text-generation-webui api endpoint
- Updated parser to match new response

---

#### Version 3.1: 2023/12/10
- Supported two text generation methods: Normal and Stream.
- Normal: Editing the message after the whole message is generated
- Stream: Update the message word by word, just like ChatGPT.

Known Issues:
- Streaming mode can cause the AI to go on forever.

---

#### Version 3.2: 2023/12/11
- Sorted global variables, removed unused ones
- New bot command: '!help' and '!joke'
- '!help': shows available commands
- '!joke': sends a random joke

In progress:
- Fix for infinite stream reply from AI.

---

#### Version 3.3: 2023/12/12
- Combined all if statements into one for statement
- Made all commands a separate function
- Provide command recommendations when a user mistypes a command by using levenshtein distance.

---

#### Version 4.0: 2023/12/19
- Added an option to test local AI server status (online / offline), and fall back to NGC service to create AI response when local server is offline or unresponding
- NGC Model: Llama 2 70B
- Added logs file to .gitignore

---

#### Version 4.1: 2023/12/28
- Added channel name when announcing message in logs
- Fixed command identifying and running process
- Added a variable to save state of local AI service, and only query on first message request
- Fixed a typo in help message
- Finished logging messages when requesting ngc
- Finished response parsing process for ngc

---

#### Version 4.2: 2023/12/28
- Modified local AI service query time to only when startup
- Always announce message in logs, even if from bot
- Actually calling the NGC response parser, and fixed bug in logging

---

#### Version 5.0: 2023/12/29
- Moved logging folder, and auto creates it if it doesn't exist
- Unified logging format (DEBUG->DEBG)
- Added NGC context chat mode
- New command: Clear context, clears server messages and bot memory

---

#### Version 5.1: 2024/01/06
- Creates main directory before bot init
- Unified Logging into a function
- Remove unneeded debug_log value check
- More detailed process description in comments
- Splits message if bot reply is over 2000 words (Discord limit)

New Command:
- context_export: Exports the message history in 'Context" channel into a text file, both save it and sends it.

---

#### Version 5.2: 2024/01/09
- Fixed naming of dictionary for context channels
- Moved log directory creation to the start of the script
- Removed sse module DEBUG messages from the log messages
- Moved AI service testing into a separate function
- Make different service in log to have different colors
- Clear comment describing each functions' usage
- '!clear context' now only clears bot's message history
- context export function now checks which history is modified, and only export modified one

New feature:
- Different channel category calls different AI endpoints(Only local and NGC for now, more to come in the future)
- Local AI now has context mode
- NGC AI now has streaming mode (Prompts user to reset history when history is too long for NGC)

New command:
- clear channel', clears the channel the command is from
- model: shows current loaded model and model available (local)
- service check: rechecks the local AI service status
- load model: loads model of choice (WIP)

---

#### Version 5.3: 2024/01/12
- Reduced repetition in sending assistance response by making it a separate function

---

#### Version 5.4: 2024/01/14
- Moved initial service check function to on_ready, so the coroutine can be run.
- Updated command identifying method to check if message starts with any of the commands, so choosing model to load can be possible.

New Command:
- load model: the command is now complete and useable.

---

#### Version 5.5: 2024/01/14
- Moved most global variables into the init function
- Overhauled status report

---

#### Version 5.6: 2024/01/17
- moved presence update into a separate function
- Updated NGC AI auth token as the old one expired (New expire date: 2024/02/16)

---

#### Version 5.7: 2024/01/18
- Created a section of variables for setting request parameters and settings for easy tweaking
- Small bug fix in ngc context mode
- Fix service name of presence update to match format

---

#### Version 5.8: 2024/01/19
- New model_args variable for loading settings for different models
- clean_string function for removing non-ascii log message characters, to prevent errors

New command:
- unload model: Unloads the current loaded model

---

#### Version 5.9: 2024/01/22
- Both context channel message history dictionary is now a class variable
- The bot now outputs the model used to generate response to the Discord channel
- Removed request data from being logged to prevent a wall of text popping up after long context chat

Notes:
- Export context command requires modifications

---

#### Version 5.10: 2024/01/26
- Optimized context message variable defining and resetting

---

#### Version 5.11: 2024/01/27
- Uses Boolean variables to track if context history is modified
- Removes unused library
- Only announces new message when it is not from the bot
- Updates edit_message to send_message function as message sending process is changed last version
- Updates clear_context function to ultilize the new way of tracking context history editing

---

#### Version 5.12: 2024/02/02
- Fixing context messages not resetting correctly after command
- Fix typos
- Set utf-8 as context export encoding format to correctly export emojis.

---

#### Version 6.0: 2024/02/02
- NGC AI models is now changeable using the same command as local models
- "!models" and "!model load" command now checks channel category to deliver replies accordingly

---

#### Version 7.0: 2024/02/02
- Complete overhaul of the AI function callings to reduce code lines
- Combined local AI normal and context function
- Combined NGC AI normal and context function

---

#### Version 7.1: 2024/02/02
- Removed logging AI prompts to increase readability of the log file.
- Small fixes to the NGC AI request function

---

#### Version 7.2: 2024/02/03
- Combined two loggging mode switching functions into one, and update help command accordingly.
- Updated message annoucing when the author is bot.
- Update the info message sent to Discord chat when waiting for a response
- Updated status request to include current AI model in the reply, and reduced duplicate lines and increase readability
- Removed request prompt and payload from logging. (NGC streaming)

---

#### Version 8.0: 2024/02/05
- Implemented asynchronous http requests to both NGC and local AI services via httpx library
- Removed sseclient as it's now unused
- Small bug fix to NGC logs

---

#### Version 8.1: 2024/02/05
- Local model names have been renamed on the server side for more readability
- AI prompt have been updated to include user id, and description of it's abilities.
- Small bug fixes to ai_request function
- Optimized ngc_ai_request to remove duplicate lines
- Slight tweaks to the model_info function

New feature:
- Now the bot will update the time elapsed since the request is made

Local AI models:
Currently supports 4 model configurations, all quantised.
- Llama 7B
-Llama 13B
-Mistral-7B
-Zephyr-7B

---

#### Version 8.2: 2024/02/06
- Updates AI prompt to include current date and weekday, and jimmyn3577 as the developer of the bot
- message.proc and message.send services is now logged with light yellow color

---

#### Version 8.3: 2027/02/07
- Implemented .env file to store API tokens for NGC and Discord. The .env file is added to .gitignore to prevent leaking to the public.
- The Discord server is now updated to have only one text-to-text category, and the bot will only reply with NGC as a fallback in case local AI is not online.

---

#### Version 8.4: 2024/02/09
- Message broadcasting now includes more info.
- Context message now marks the user id, so different can cha with the model in parallel.
- The script can now handle local AI server suddenly goes offline.
- Context exporting is updated to also export the specific user's context only.
- update_time function now only use a variable to add one every second, preventing the previous approach to skip a number due to number rounding.
- weekday and current date calculating is now a separate function.

---

#### Version 9.0: 2024/02/10
- context and images folder is also created on launch.

New Feature:
- AI image generating via NGC is now implemented! Currently using SDXL-Turbo as backend model.

---

#### Version 10.0: 2024/02/11
- Fixes small bug in context_messages variable defining for NGC mode
-Help message sending code have been modified to improve readability
- Fixes clear_context erroring
- Fixes NGC image generating from raising connection error exception

New Feature:
- auto_service_check: The bot now checks local AI service status every five minutes automatically
- stop_bot: Stops the bot.
- update_bot: Performs git pull to update the bot, then calls restart.py to restart the bot to apply the update.

New Command:
-!end: Stops the bot. Only jimmyn3577 is authorized to use it.
-!update: Updates the bot to the latest version, and then restarts. Only jimmyn3577 is authorized to use it.

---

#### Version 10.1: 2024/02/12
- log messages now supports logging emoji and Chinese characters

New Feature:
- restart_bot: Restarts the bot without git pull, useful for local testing

---

#### Version 11.0: 2024/02/19
- Image generating model changed from SDXL-Turbo to SDXL, since NGC no longer supports the former
- Logger setup is run outside the bot code

New Feature:
- Commands is transitioning to slash commands instead of ! as prefix
- slash-commands.py is used to handle slash commands only
- update.py to update both the bot and slash-command.py

API endpoints:
- /api - Not used yet
- /api/status - For "/status" command
- /api/service_mode - Checking current AI service provider
- /api/current_model_local - Check loaded local AI model
- /api/ngc/models - Get Available NGC models
- /api/ngc/currnet_model - Check loaded NGC AI model
- /api/ngc/load_model - Load selected NGC AI model
- /api/stop - Stops the bot and the API server

---

#### Version 11.1: 2024/02/20
- get_next_filename now also requires file extension input, in order to support more usage
- Fix error in image generation doing duplicate requests
- Image saving supports renaming to generic name when prompt is too long.

---

#### Version 11.2: 2024/02/20
- Small bug fix for bot logging method and image generation
- Update restart script and update to use powershell instead of cmd
- logging is now implemented for slash-command script
- Migrated restart command to slash command

---

#### Version 11.3: 2024/02/20
- Quick fix in error on logging function for slash-command script.

---

#### Version 11.4: 2024/02/20
- Another hotfix for logging in slash-commands script

---

#### Version 11.5: 2024/02/20
- Image generated is now saved with a generic name, with the prompt saved in a separate file

---

#### Version 11.6: 2024/02/21
- Stops bot responding outside intended channels
- Combined AI request and response into one function
- Fixed restart and update script

---

#### Version 11.7: 2024/02/22
- Changed NGC default model to mixtral-8x7b-instruct as the output is much better
- Removed unused sse code and libraries
- Every user now gets their context history prepared the first time they sent an AI request, no matter the service called
- Context clearing and exporting is now merged to slash command

---

#### Version 11.8: 2024/02/23
- Merged status report command to slash command, and removed joke command as it's unused
- Tewake help command output to remove merged command
- Removed old context export code
- Added NGC images response count in status report

---

#### Version 11.9: 2024/02/23
- Merged debug log and service check commands to slash commands
- Retired all ! prefix commands

---

#### Version 11.9.1: 2024/02/23
- Restored service_check function for auto service check

---

#### Version 11.10: 2024/02/23
- Added Gemma-7b and Mamba-Chat to NGC models

---

#### Version 12.0: 2024/02/24
- Support for local stable diffusion image generation is here!
- Service check function now also checks the local image service
- Service selection now only selects loacl if status code is 200

---

#### Version 12.1: 2024/02/24
- Image prompts file and image is now stored in separate directories
- Status report now includes AI image service status
- Service update API endpoint now supports updating image service status

---

#### Version 12.2: 2024/02/24
- /imagegenrank: Shows the ranking of different user image generation amounts

---

#### Version 12.3: 2024/02/24
- Small bug fix for /status command

---

#### Version 12.4: 2024/02/24
- /imagegenrank now sorts user by the value, high to low

---

#### Version 12.5: 2024/02/27
- Removed unused library
- Updated context messages variables initializing
- AI request now retries for 5 times after an error before raising error message to channel
- ai_response_image now retries no matter the exceptions

---

#### Version 12.6: 2024/02/29
- Patched bug in message context variable initializing

---

#### Version 13.0: 2024/03/02
- /status command now shows current version number and date
- Fixed bug in local context messages bool variable

New Feature:
- Google's Gemini AI model is now available to use in 'google-gemini' chat category, currently only text to text and no context awareness. More feautres to come in a future release

---

#### Version 13.1: 2024/03/02
- Fixed error that makes AI request 5 times even the request is successful
- Handles Gemini errors by checking if the prompt was blocked

---

#### Version 13.2: 2024/03/05
- Fixed name for NGC mistral model
- Removed unnecessary messages when Gemini blocks a request

New Feature:
- Context mode for Google Gemini

---

#### Version 13.2.1: 2024/03/05
Hot fix for name updating for NGC AI model.

---

#### Version 13.2.2: 2024/03/05
Hot fix for version name error

---

#### Version 13.3: 2024/03/05
- clear context command now also clears Gemini context

---

#### Version 13.4: 2024/03/07
- Fixed bot not correctly exiting after a command call to do so.

---

#### Version 13.5: 2024/03/09
- Bot's variables will be saved to a pickle file to be loaded on next startup, achieving no memory loss when restarted
- Response counts variables for different services is now combined into one

---

#### Version 14.0: 2024/03/10
- Removed unnecessary file from the repository

New Feature:
- Google Gemini Vision model is now implemented, so the AI can now read and describe pictures

---

#### Version 14.1: 2024/03/11
- The bot now correctly resets presence after an Gemini request
- Stream channels now updates every 10 chunks to increase speed previously bottlenecked by the Discord API
- Status message formatting fixed

---

#### Version 14.2: 2024/03/15
- Handles Gemini blocking response under context mode

New Features:
- /pausebot: the bot can be paused, ignoring all incoming request and commands except /pausebot

---

#### Version 14.3: 2024/03/15
- Update code to initialize Gemini chat when user id not in context message variable or used bool flag == False
- Fixes bug in bot always returning blocked after /clearcontext
- Fixed a typo in Gemini error message

---

#### Version 15.0: 2024/03/15
- Image generations is now sent via embed messages, with some more insights included

---

#### Version 15.1: 2024/03/15
- Image embeds now includes bot version in footer
- /status and /imagegenrank now also replies via embeds

---

#### Version 15.2: 2024/03/17
- Fixed bug that causes local AI request to repeat 5 times even after a successful request
- Updated embed footer for image generation
- Update presence update method
- Fixed error in /model load command

---

#### Version 15.3: 2024/03/21
- /status endpoint now correctly displays local AI model name when using local inference server
- /announce now correctly displays newline message

---

#### Version 16.0: 2024/03/22
- Big revamp for NGC AI requesting as Nvidia changed their service.
- Stream mode is deprecated and it's code and channels will be removed in a later release

---

#### Version 16.1: 2024/03/22
- Fixed errors in the API server of the bot not updating to new NGC text model structure.

---

#### Version 16.1.1: 2024/03/22
Hot fix for yet another bug in /status API endpoint

---

#### Version 16.2: 2024/03/24
- Stream mode is fully deprecated
- Gemini now logs with color light cyan
- handles Gemini generation error by retrying, and raised the error after 5 failed attempts
- Gemini context responses is now also counted

---

#### Version 17.0: 2024/03/25
- The bot now correctly remembers chat history
- Handles Gemini request failing and block differently and correctly
- /clearcontext now clears different context based on the channel they're from, and prompts the user with 'no context history for this channel' when not in context channels

New Feature:
- Text adventure channel and mode: You can now play a text adventure game with the bot! The chat history of this mode is per channel instead of per user

---

#### Version 17.1: 2024/03/25
New Feature:
- Story teller mode, where the AI will write a story based on your prompt

---

#### Version 17.2: 2024/03/31
Changes:
- The AI tokens limit is bumped to 1024, should fix the error where the AI randomly stops in a sentence
- Personality modes now supports local AI service

---

#### Version 17.3: 2024/03/31
Changes:
- Finished logging setup for personality AI mode
- Improved efficiency of directory creating function

---

#### Version 17.4: 2024/04/01
Changes:
- Personality AI mode now supports both normal (Local/NGC) or Gemini as backend inference service, Gemini is the default
- /personality to adjust inference service
- Changed Gemini context mode context saving and sending function to achieve no memory loss when restarting bot, as the old method can't be saved

---

#### Version 18.0: 2024/04/01
New Feature:
- The bot now offers a new feature, image to video! It takes a still image as prompt, and generated a 4 second clip from it!

---

#### Version 18.1: 2024/04/04
Changes:
- Refined log messages from various processes
- Optimized code for sending image via embed message
- The bot now replies to user request with progress of the request
- Handles Google Gemini request failing or blocked in personality AI mode
- Handles image to video request failing
- Fixed bug in Gemini image requests

---

#### Version 19.0: 2024/04/08
Changes:
- Fully deprecated Nvidia NGC API usage as my account credits are fully depleted and unusable. From now on, only local inference will be available to the bot unless I find another free AI API service

---

#### Version 19.1: 2024/04/08
Changes:
- Hot fix for bug in AI text request processing

---

#### Version 20: 2024/04/18
New Features:
- text-to-music: The bot can now generate a five second audio clip from text prompts

- text-to-video: The bot can now generate a gif video from text prompts

- inference-server.py: This script is used to run T2M and T2V models locally on my laptop, and serve requests over an API endpoint. T2M uses musicgen-stereo-medium as the backend AI model, while T2V uses AnimateDiff-Lightning as the backend AI model.

---

#### Version 20.1: 2024/04/21
Changes:
- /status report now includes stats for now music and video generation, along with the status of the inference server
- clear_context() function is now updated to discard old NGC code, as well as overhaul of the whole function to increase modularity and readability

---

#### Version 20.2: 2024/04/22
Changes:
- New model supported: Llama 3 8B Instruct, also quantised
- AI text non-context requests updated to make Llama 3 work
- Service check task updated to handle service checking the same time the text server is busy with a request, which will return timeout

---

#### Version 21: 2024/04/28
Changes:
- inference server code overhauled to include STT (Speech to Text) and TTS (Text to Speech) functions, and option to unload or load any services (STT, TTS, TTM, TTV). Model loading and unloading also updated to be a class object.
- /inferenceserver command to access inference server options such as loaded services, and load or unload services

New Feature:
- Voice chat assistant (Experimental). Due to Discord API limitations and mobile app's lack of support for playing audio files natively, the new mode is made possible with Streamlit. Using Streamlit along with Ngrok free tier, now any user can submit a voice recording, and the assistant will reply using Parler-TTS.
- Voice chat assistant is currently single-turn only, with multi-turn conversation planned and under development.

---

#### Version 21.1: 2024/04/29
Changes:
- The voice chat now supports multi-turn conversations!
- Added some info and warning texts.

---

#### Version 21.2: 2024/05/15
Changes:
- Inference server updates to improve performance of text to speech endpoint.

Voice chat page updates:
- Changed audio recorder to fix issue of inability to record after submitting once

Repository updates:
- New README.md file to introduce the repository
- Added `__pycache__` to .gitignore

---

#### Version 22.0: 2024/05/22
Changes:
- Google Gemini models have been updated to the latest available on the API. Normal text interactions now uses `Gemini 1.5 Flash`, and requests with image uses `Gemini 1.5 Pro`.
- Google Gemini requesting is now in an async function, preventing a longer request hanging the bot.
</details>