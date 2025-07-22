import asyncio
import logging
import numpy as np
import ffmpeg
import os
from faster_whisper import WhisperModel

from backend.schemas.request import STTRequest
from backend.services.queues import stt_input_queue, stt_output_queue

log = logging.getLogger(__name__)
logging.getLogger("faster_whisper").setLevel(logging.WARNING)

def _transcribe_audio(model, audio_chunk):
    # This is a blocking, CPU-bound function
    try:
        pcm_out, _ = (
            ffmpeg
            .input('pipe:0', format='webm')
            .output('pipe:1', format='s16le', acodec='pcm_s16le', ac=1, ar=16000)
            .run(input=audio_chunk, capture_stdout=True, capture_stderr=True)
        )
        float32_audio = np.frombuffer(pcm_out, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = model.transcribe(float32_audio, beam_size=5, language="ko", vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
        return "".join(seg.text for seg in segments)
    except ffmpeg.Error as e:
        log.error(f"FFmpeg 오류: {e.stderr.decode()}")
        return None

async def stt_worker():
    loop = asyncio.get_running_loop()
    model = WhisperModel("small", device="cpu", compute_type="int8")
    log.info("STT 워커가 시작되었습니다.")

    while True:
        try:
            req: STTRequest = await stt_input_queue.get()
            if req is None: break

            # Run the blocking ffmpeg and model transcription in an executor
            stt_text = await loop.run_in_executor(
                None, _transcribe_audio, model, req.chunk
            )

            if stt_text and stt_text.strip():
                log.info(f"[{os.getpid()}] STT 변환 완료: {stt_text}")
                await stt_output_queue.put((req.client_id, req.target_lang, stt_text))

        except Exception as e:
            log.error(f"STT 워커 오류: {e}")
        finally:
            stt_input_queue.task_done()

