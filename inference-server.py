import torch
import soundfile as sf
from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor, AutoTokenizer
import os
from flask import Flask, jsonify, request, send_file
import io
from waitress import serve
from diffusers import  AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
from diffusers.utils import export_to_gif
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
from parler_tts import ParlerTTSForConditionalGeneration
from werkzeug.utils import secure_filename
import base64

# Detect server environment
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Initialize AI model loader
class Model_Loader:
    """Load AI models for inference server."""
    def __init__(self):
        """Initialize AI models.
        Args:
            stt_model_name: Speech-to-Text model name.
            ttm_model_name: Text-to-Music model name.
            ttv_repo_name: Text-to-Video repository name.
            ttv_base_name: Text-to-Video base name.
            ttv_ckpt_name: Text-to-Video checkpoint name.
            stt_loaded: Speech-to-Text model loaded status.
            ttm_loaded: Text-to-Music model loaded status.
            ttv_loaded: Text-to-Video model loaded status."""
        
        self.stt_model_name = "openai/whisper-large-v3"
        self.ttm_model_name = "facebook/musicgen-stereo-medium"
        self.ttv_repo_name =  "ByteDance/AnimateDiff-Lightning"
        self.ttv_base_name = "fluently/Fluently-v4"
        self.ttv_ckpt_name = "animatediff_lightning_2step_diffusers.safetensors"
        self.tts_model_name = "parler-tts/parler_tts_mini_v0.1"
        self.stt_loaded = False
        self.ttm_loaded = False
        self.ttv_loaded = False
        self.tts_loaded = False
    
    def load_stt(self):
        """Load Speech-to-Text model. Returns already loaded message if model is already loaded."""
        if not self.stt_loaded:
            print("Loading whisper-large-v3")
            self.stt_model = AutoModelForSpeechSeq2Seq.from_pretrained(self.stt_model_name, torch_dtype=torch.float32, low_cpu_mem_usage=True, use_safetensors=True)
            self.stt_model.to("cpu")
            self.stt_processor = AutoProcessor.from_pretrained(self.stt_model_name)
            self.stt_pipe = pipeline("automatic-speech-recognition", model=self.stt_model, tokenizer=self.stt_processor.tokenizer, feature_extractor=self.stt_processor.feature_extractor, max_new_tokens=128, chunk_length_s=30, batch_size=16, return_timestamps=True, torch_dtype=torch.float32, device="cpu")
            self.stt_loaded = True
            print("whisper-large-v3 loaded")
            return "success"
        else:
            print("whisper-large-v3 already loaded")
            return "already loaded"
    
    def load_ttm(self):
        """Load Text-to-Music model. Returns already loaded message if model is already loaded."""
        if not self.ttm_loaded:
            print("Loading musicgen-stereo-medium")
            self.ttm_model = pipeline("text-to-audio", self.ttm_model_name, device=device, torch_dtype=torch_dtype)
            self.ttm_loaded = True
            print("musicgen-stereo-medium loaded")
            return "success"
        else:
            print("musicgen-stereo-medium already loaded")
            return "already loaded"
    
    def load_ttv(self):
        """Load Text-to-Video model. Returns already loaded message if model is already loaded."""
        if not self.ttv_loaded:
            print("Loading AnimateDiff-Lightning")
            self.ttv_adapter = MotionAdapter().to(device=device, dtype=torch_dtype)
            self.ttv_adapter.load_state_dict(load_file(hf_hub_download(self.ttv_repo_name, self.ttv_ckpt_name),device="cuda"))
            self.ttv_model = AnimateDiffPipeline.from_pretrained(self.ttv_base_name, motion_adapter=self.ttv_adapter, torch_dtype=torch.float16).to("cuda")
            self.ttv_model.scheduler = EulerDiscreteScheduler.from_config(self.ttv_model.scheduler.config, timestep_spacing="trailing", beta_schedule="linear")
            self.ttv_loaded = True
            print("AnimateDiff-Lightning loaded")
            return "success"
        else:
            print("AnimateDiff-Lightning already loaded")
            return "already loaded"

    def load_tts(self):
        """Load Text-to-Speech model. Returns already loaded message if model is already loaded."""
        if not self.tts_loaded:
            print("Loading parler-tts")
            self.tts_model = ParlerTTSForConditionalGeneration.from_pretrained(self.tts_model_name).to(device)
            self.tts_tokenizer = AutoTokenizer.from_pretrained(self.tts_model_name)
            self.tts_loaded = True
            print("parler-tts loaded")
            return "success"
        else:
            print("parler-tts already loaded")
            return "already loaded"

    def load_model(self, service_name):
        """Load AI model based on service name."""
        #if sum([self.stt_loaded, self.ttm_loaded, self.ttv_loaded, self.tts_loaded]) > 1:
            #print("2 Models already loaded. Unload one before loading another.")
            #return "model count exceeded"
        if service_name == "stt":
            result = self.load_stt()
            return result
        elif service_name == "ttm":
            result = self.load_ttm()
            return result
        elif service_name == "ttv":
            result = self.load_ttv()
            return result
        elif service_name == "tts":
            result = self.load_tts()
            return result
        else:
            print("Invalid service name")
            return "invalid service name"
    
    def unload_model(self, service_name):
        """Unload AI model based on service name."""
        if service_name == "stt":
            if self.stt_loaded:
                del self.stt_model, self.stt_processor, self.stt_pipe
                self.stt_loaded = False
                return "success"
            else:
                return "already unloaded"
        elif service_name == "ttm":
            if self.ttm_loaded:
                del self.ttm_model
                self.ttm_loaded = False
                return "success"
            else:
                return "already unloaded"
        elif service_name == "ttv":
            if self.ttv_loaded:
                del self.ttv_adapter, self.ttv_model
                self.ttv_loaded = False
                return "success"
            else:
                return "already unloaded"
        elif service_name == "tts":
            if self.tts_loaded:
                del self.tts_model, self.tts_tokenizer
                self.tts_loaded = False
                return "success"
            else:
                return "already unloaded"
        else:
            return "invalid service name"

model_loader = Model_Loader()

# Initialize Flask API server
app = Flask(__name__)

# https://server:port/status
@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'online'})

# https://server:port/musicgen
@app.route('/musicgen', methods=['POST'])
def musicgen():
    if model_loader.ttm_loaded:
        prompt = request.json['prompt']
        music = model_loader.ttm_model(prompt, forward_params={"max_new_tokens": 256})
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
    else:
        return jsonify({'error': 'Model not loaded'}), 503

# https://server:port/text2video
@app.route('/text2video', methods=['POST'])
def text2video():
    if model_loader.ttv_loaded:
        prompt = request.json['prompt']
        video = model_loader.ttv_model(prompt, guidance_scale=1.0, num_inference_steps=2)
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
    else:
        return jsonify({'error': 'Model not loaded'}), 503

# https://server:port/speech2text

@app.route('/speech2text', methods=['POST'])
def speech2text():
    if model_loader.stt_loaded:
        data = request.get_json()
        if 'file' not in data:
            return jsonify({'error': 'No file part in the request'}), 400
        file_data = base64.b64decode(data['file'])
        file = io.BytesIO(file_data)
        filename = secure_filename("input.wav")
        with open(filename, 'wb') as f:
            f.write(file.getbuffer())
        result = model_loader.stt_pipe(filename)
        os.remove(filename)
        return jsonify({'text': result["text"]})
    else:
        return jsonify({'error': 'Model not loaded'}), 503

# https://server:port/text2speech
@app.route('/text2speech', methods=['POST'])
def text2speech():
    if model_loader.tts_loaded:
        prompt = request.json['prompt']
        description = "A male friendly voice with a medium pitch and a moderate pace. The speaker sounds very expressive and speaks in a very clear and articulate manner."
        input_ids = model_loader.tts_tokenizer(description, return_tensors="pt").input_ids.to(device)
        prompt_input_ids = model_loader.tts_tokenizer(prompt, return_tensors="pt").input_ids.to(device)
        generation = model_loader.tts_model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
        audio_arr = generation.cpu().numpy().squeeze()
        sf.write("text2speech_out.wav", audio_arr, model_loader.tts_model.config.sampling_rate)
        try:
            with open("text2speech_out.wav", 'rb') as f:
                data = f.read()
            os.remove("text2speech_out.wav")
            return send_file(
                io.BytesIO(data),
                mimetype='audio/wav',
                as_attachment=True,
                download_name="text2speech_out.wav"
            )
        except Exception as e:
            return str(e)
    else:
        return jsonify({'error': 'Model not loaded'}), 503

# https://server:port/models
@app.route('/models', methods=['GET'])
def models():
    return jsonify({'stt_loaded': model_loader.stt_loaded, 'ttm_loaded': model_loader.ttm_loaded, 'ttv_loaded': model_loader.ttv_loaded, 'tts_loaded': model_loader.tts_loaded})

# https://server:port/load_model
@app.route('/load_model', methods=['POST'])
def load_model():
    service_name = request.json['service_name']
    result = model_loader.load_model(service_name)
    return jsonify({'status': result})

# https://server:port/unload_model
@app.route('/unload_model', methods=['POST'])
def unload_model():
    service_name = request.json['service_name']
    result = model_loader.unload_model(service_name)
    return jsonify({'status': result})

if __name__ == '__main__':
    model_loader.load_model("ttm")
    model_loader.load_model("ttv")
    model_loader.load_model("stt")
    model_loader.load_model("tts")
    serve(app, host='0.0.0.0', port=6000)