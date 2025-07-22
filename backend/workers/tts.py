import asyncio
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
}

def _synthesize_audio(tts_model, text, samplerate):
    # This is a blocking, CPU/GPU-bound function
    audio_array = tts_model.tts(text=text)
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, samplerate, format="WAV")
    return buffer.getvalue()

async def tts_worker():
    loop = asyncio.get_running_loop()
    log.info("TTS 워커가 시작되었습니다.")

    while True:
        try:
            req: TTSRequest = await tts_input_queue.get()
            if req is None: break

            tts_model = tts_models_map.get(req.target_lang)
            if not tts_model:
                log.warning(f"지원하지 않는 TTS 언어입니다: {req.target_lang}")
                continue

            samplerate = tts_model.synthesizer.output_sample_rate

            # Run the blocking TTS synthesis and file operations in an executor
            audio_bytes = await loop.run_in_executor(
                None, _synthesize_audio, tts_model, req.translated, samplerate
            )

            if audio_bytes:
                response = StsResponse(
                    client_id=req.client_id,
                    target_lang=req.target_lang,
                    translated_text=req.translated,
                    audio_bytes=audio_bytes
                )
                await tts_output_queue.put(response)
                log.info(f"[{os.getpid()}] TTS 완료: text={req.translated!r} => {len(audio_bytes)} bytes")

        except Exception as e:
            log.error(f"[{os.getpid()}] TTS 처리 중 오류: {e}")
        finally:
            tts_input_queue.task_done()
