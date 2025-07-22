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

    try:
        while True:
            chunk = await websocket.receive_bytes()
            req = STTRequest(
                client_id=client_id,
                target_lang=target_lang,
                chunk=chunk
            )
            await stt_input_queue.put(req)
    except WebSocketDisconnect:
        log.info(f"[{client_id}] 연결 종료 (채널: {target_lang})")
    finally:
        manager.disconnect(target_lang, websocket)