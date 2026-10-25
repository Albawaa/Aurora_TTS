import os
import time
import torch
import warnings
import soundfile as sf
import logging
from pathlib import Path
import numpy as np

LOGGER = logging.getLogger(Path(__file__).name)
PROJECT_DIR = Path(__file__).parents[2].resolve()
LOG_DIR = PROJECT_DIR / "temp_logs" # Log directory where TTS text and audio are saved. 
LOG_DIR.mkdir(parents=True, exist_ok=True)


class KokoroTTSHandler:
    '''
    Handles the TTS generation with KokoroTTS.
    '''
    def __init__(self):
        # Quiet down the startup clutter and lock to offline mode
        os.environ["HF_HUB_OFFLINE"] = "1"
        warnings.filterwarnings("ignore",
                                category=UserWarning,
                                module="torch.nn.modules.rnn")
        warnings.filterwarnings("ignore", 
                                category=FutureWarning, 
                                module="torch.nn.utils.weight_norm")

        user_home = os.path.expanduser("~")
        cache_dir = os.path.join(
            user_home, 
            ".cache", "huggingface", "hub", 
            "models--hexgrad--Kokoro-82M", "snapshots"
        )

        # Find the long alphanumeric snapshot subfolder automatically
        snapshot_folder = os.listdir(cache_dir)[0]
        voices_path = os.path.join(cache_dir, snapshot_folder, "voices")

        # Uncomment following line to view where tts is reading voice files from, commented to avoid terminal clutter
        # LOGGER.debug(f"Reading voice blueprints from: {voices_path}") 

        LOGGER.info("Initializing Kokoro TTS Engine... Please wait a moment.")

        from kokoro import KPipeline
        self.pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
        LOGGER.info("Kokoro TTS Engine ready :3")

        # Load the target voice matrices directly from disk using Torch
        voice_a_file = os.path.join(voices_path, "af_nova.pt")
        voice_b_file = os.path.join(voices_path, "am_fenrir.pt")
        voice_c_file = os.path.join(voices_path, "zf_xiaoxiao.pt")

        # good mixes:
        # soft whisper like, girl: af_nicole 0.70 bm_lewis 0.30
        # energetic young adult, boy: af_nova 0.35 am_fenrir 0.80 (yes >1)
        # nice asmr: af_nicole 0.50, zf_xiaoxiao.pt 0.6 (yes >1)
        # a tts sounding voice: af_nova 0.33, am_fenrir 0.33, zf_xiaoxiao 0.33
        
        voice_a_tensor = torch.load(voice_a_file, map_location="cpu", weights_only=True)
        voice_b_tensor = torch.load(voice_b_file, map_location="cpu", weights_only=True)
        voice_c_tensor = torch.load(voice_c_file, map_location="cpu", weights_only=True)

        # Mathematically mix the voice vectors (Must add up to 1.0 total)
        weight_a = 0.33
        weight_b = 0.33
        weight_c = 0.33
        self.current_voice = (voice_a_tensor * weight_a) + (voice_b_tensor * weight_b) + (voice_c_tensor * weight_c)


    def generate_audio_file(self, user_text: str) -> str:
        '''
        Runs KokoroTTS inference with received text.
        Parameter:
            - user_text(str): Text to be converted to speech.
        Returns:
            - str: Generated audio file name.
        '''
        LOGGER.info("Synthesizing...")
        inference_start = time.perf_counter()

        # Generate the audio array
        generator = self.pipeline(user_text, voice=self.current_voice, speed=1.0)
        results = list(generator)

        inference_time = time.perf_counter() - inference_start
        LOGGER.info(f" Done in {inference_time:.4f} seconds!")

        # Save all processed segments into a single file loop
        audio_chunks = [audio for (_, _, audio) in results if audio is not None]

        if not audio_chunks:
            LOGGER.warning("No audio was generated")
            output_filepath = ""
        else:
            full_audio = np.concatenate(audio_chunks)

            ns_timestamp = time.time_ns()
            output_filename = f"live_output_{ns_timestamp}.wav"
            output_filepath = LOG_DIR / output_filename
            sf.write(output_filepath, full_audio, 24000)
            LOGGER.info(f" Saved to: {output_filepath}")

        return output_filename
