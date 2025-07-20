import logging
import numpy as np
import ffmpeg
import os
from faster_whisper import WhisperModel

from backend.schemas.request import STTRequest
from backend.services.queues import stt_input_queue, stt_output_queue

log = logging.getLogger(__name__)

def stt_worker():
    log.warning(f"[{os.getpid()}] STT 워커 시작. 모델 로딩...")
    model = WhisperModel("base", device="cpu", compute_type="int8")

    while True:
        try:
            req: STTRequest = stt_input_queue.get()
            if req is None: break

            log.warning(f"[{os.getpid()}] 클라이언트 {req.client_id}의 STT 작업 처리 시작...")
            try:
                pcm_out, _ = (
                    ffmpeg
                    .input('pipe:0', format='webm')
                    .output('pipe:1', format='s16le', acodec='pcm_s16le', ac=1, ar=16000)
                    .run(input=req.chunk, capture_stdout=True, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                log.warning(f"FFmpeg 오류: {e.stderr.decode()}")
                continue

            float32_audio = np.frombuffer(pcm_out, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = model.transcribe(float32_audio, beam_size=5)
            stt_text = "".join(seg.text for seg in segments)

            if stt_text.strip():
                log.warning(f"[{os.getpid()}] STT 변환 완료: {stt_text}")
                stt_output_queue.put((req.client_id, req.target_lang, stt_text))

        except Exception as e:
            log.error(f"STT 워커 오류: {e}")
