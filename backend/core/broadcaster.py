import asyncio
import base64
import logging
from queue import Empty

from backend.services.ConnectionManager import manager
from backend.services.queues import tts_output_queue

log = logging.getLogger(__name__)

def safe_get(queue, timeout=1):
    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None

async def broadcast2():
    log.warning("[Broadcaster] 시작.")
    loop = asyncio.get_running_loop()

    while True:
        response = await loop.run_in_executor(None, lambda: safe_get(tts_output_queue))

        if response is None:
            await asyncio.sleep(0.01)
            continue

        log.warning(f"방송 작업 수신: client_id={response.client_id}")
        await manager.broadcast_bytes(response.client_id, response.target_lang, response.audio_bytes)

async def broadcast():
    log.warning("[Broadcaster] 시작.")
    loop = asyncio.get_running_loop()

    while True:
        response = await loop.run_in_executor(None, lambda: safe_get(tts_output_queue))

        if response is None:
            await asyncio.sleep(0.01)
            continue

        log.warning(f"방송 작업 수신: client_id={response.client_id}")

        # --- 💡 프론트엔드로 보낼 JSON 데이터 생성 💡 ---
        # 1. 오디오 바이트를 Base64 문자열로 인코딩
        audio_b64 = base64.b64encode(response.audio_bytes).decode('utf-8')

        # 2. 전송할 데이터 묶음(딕셔너리) 생성
        payload = {
            "client_id": response.client_id,
            "translated_text": response.translated,  # 번역된 텍스트
            "audio_bytes_b64": audio_b64  # Base64 인코딩된 오디오
        }

        # --- 💡 새로 만든 broadcast_json 함수 호출 💡 ---
        await manager.broadcast_json(response.target_lang, payload)