import io
import logging
import os
import soundfile as sf
from TTS.api import TTS
import torch

from backend.schemas.request import TTSRequest
from backend.schemas.response import StsResponse
from backend.services.queues import tts_input_queue, tts_output_queue

log = logging.getLogger(__name__)

device = "cuda" if torch.cuda.is_available() else "cpu"

tts_models_map = {
    "en": TTS(model_name="tts_models/en/ljspeech/vits", progress_bar=False).to(device),
    "es": TTS(model_name="tts_models/es/css10/vits", progress_bar=False).to(device),
    #"ja": TTS(model_name="tts_models/ja/kokoro/tacotron2-DDC", progress_bar=False).to(device),
    #"zh-cn": TTS(model_name="tts_models/zh-CN/baker/tacotron2-DDC-GST", progress_bar=False).to(device),
    #"fr": TTS(model_name="tts_models/fr/css10/vits", progress_bar=False).to(device),
}

def tts_worker():
    while True:
        req: TTSRequest = tts_input_queue.get()
        if req is None: break
        tts_model = tts_models_map[req.target_lang]

        try:
            samplerate = tts_model.synthesizer.output_sample_rate
            audio_array = tts_model.tts(text=req.translated)

            buffer = io.BytesIO()
            sf.write(buffer, audio_array, samplerate, format="WAV")
            audio_bytes = buffer.getvalue()

            if audio_bytes:
                response = StsResponse(
                    client_id=req.client_id,
                    target_lang=req.target_lang,
                    translated_text=req.translated,
                    audio_bytes=audio_bytes
                )
                tts_output_queue.put(response)
                log.info(f"[{os.getpid()}] TTS 완료: text={req.translated!r} => {len(audio_bytes)} bytes")

        except Exception as e:
            log.error(f"[{os.getpid()}] TTS 처리 중 오류: {e}")
