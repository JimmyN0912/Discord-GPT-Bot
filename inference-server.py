import torch
import soundfile as sf
from transformers import pipeline
import os
from flask import Flask, jsonify, request, send_file
import io
from waitress import serve
from diffusers import  AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
from diffusers.utils import export_to_gif
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

# Start AI models
print("Loading musicgen-stereo-medium")
synthesiser = pipeline("text-to-audio", "facebook/musicgen-stereo-medium", device="cuda:0", torch_dtype=torch.float16)
print("musicgen-stereo-medium loaded")
print("Loading AnimateDiff-Lightning")
adapter = MotionAdapter().to(device="cuda", dtype=torch.float16)
adapter.load_state_dict(load_file(hf_hub_download("ByteDance/AnimateDiff-Lightning", "animatediff_lightning_2step_diffusers.safetensors"),device="cuda"))
AnimateDiff_Lightning = AnimateDiffPipeline.from_pretrained("emilianJR/epiCRealism", motion_adapter=adapter, torch_dtype=torch.float16).to("cuda")
AnimateDiff_Lightning.scheduler = EulerDiscreteScheduler.from_config(AnimateDiff_Lightning.scheduler.config, timestep_spacing="trailing", beta_schedule="linear")
print("AnimateDiff-Lightning loaded")

app = Flask(__name__)

# https://server:port/status
@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'online'})

# https://server:port/musicgen
@app.route('/musicgen', methods=['POST'])
def musicgen():
    prompt = request.json['prompt']
    music = synthesiser(prompt, forward_params={"max_new_tokens": 256})
    output = "musicgen_out.wav"
    sf.write("musicgen_out.wav", music["audio"][0].T, music["sampling_rate"])
    try:
        with open(output, 'rb') as f:
            data = f.read()
        os.remove(output)
        return send_file(
            io.BytesIO(data),
            mimetype='audio/wav',
            as_attachment=True,
            download_name="musicgen_out.wav"
        )
    except Exception as e:
        return str(e)

# https://server:port/text2video
@app.route('/text2video', methods=['POST'])
def text2video():
    prompt = request.json['prompt']
    video = AnimateDiff_Lightning(prompt, guidance_scale=1.0, num_inference_steps=2)
    export_to_gif(video.frames[0], "text2video_out.gif")
    try:
        with open("text2video_out.gif", 'rb') as f:
            data = f.read()
        os.remove("text2video_out.gif")
        return send_file(
            io.BytesIO(data),
            mimetype='image/gif',
            as_attachment=True,
            download_name="text2video_out.gif"
        )
    except Exception as e:
        return str(e)
    

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=6000)