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