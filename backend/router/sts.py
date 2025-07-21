import logging
import asyncio  # asyncio 모듈을 임포트합니다.

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.schemas.request import STTRequest
from backend.services.ConnectionManager import manager
from backend.services.queues import stt_input_queue

log = logging.getLogger(__name__)
sts_router = APIRouter(prefix="/api/v1")


@sts_router.websocket("/ws/{target_lang}/{client_id}")
async def start_stream(websocket: WebSocket, target_lang: str, client_id: str):
    log.info(f"[{client_id}] 연결 (채널: {target_lang})")
    await manager.connect(target_lang, websocket)

    # 현재 실행 중인 이벤트 루프를 가져옵니다.
    loop = asyncio.get_running_loop()

    try:
        while True:
            chunk = await websocket.receive_bytes()
            req = STTRequest(
                client_id=client_id,
                target_lang=target_lang,
                chunk=chunk
            )
            # loop.run_in_executor를 사용하여 별도의 스레드에서 put을 실행합니다.
            # 이를 통해 이벤트 루프가 블로킹되는 것을 방지합니다.
            await loop.run_in_executor(None, stt_input_queue.put, req)

    except WebSocketDisconnect:
        log.warning(f"[{client_id}] 연결 종료 (채널: {target_lang})")
    finally:
        manager.disconnect(target_lang, websocket)