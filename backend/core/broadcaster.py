import asyncio
import base64
import logging

from backend.schemas.response import StsResponse
from backend.services.ConnectionManager import manager
from backend.services.queues import tts_output_queue

log = logging.getLogger(__name__)

async def broadcast():
    """
    TTS 결과를 클라이언트에게 브로드캐스팅하는 코루틴
    """
    while True:
        try:
            # asyncio.Queue에서 직접 비동기적으로 결과를 기다림
            response: StsResponse = await tts_output_queue.get()

            # 프론트엔드로 보낼 JSON 데이터 생성
            # 1. 오디오 바이트를 Base64 문자열로 인코딩
            audio_b64 = base64.b64encode(response.audio_bytes).decode('utf-8')

            # 2. 전송할 데이터 묶음(딕셔너리) 생성
            payload = {
                "client_id": response.client_id,
                "translated_text": response.translated_text,
                "audio_bytes_b64": audio_b64
            }

            # 특정 클라이언트에게만 개인 메시지 전송
            await manager.send_personal_json(
                response.target_lang,
                response.client_id,
                payload
            )

            # 작업이 완료되었음을 큐에 알림
            tts_output_queue.task_done()

        except asyncio.CancelledError:
            log.info("Broadcast task is cancelled.")
            break
        except Exception as e:
            log.error(f"Broadcasting 중 오류 발생: {e}")
            # 오류 발생 시 잠시 대기 후 계속
            await asyncio.sleep(0.1)