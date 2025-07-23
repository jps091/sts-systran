import json
import logging
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

log = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # 구조 변경: { "target_lang": { "client_id": websocket } }
        self.active_channels: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, target_lang: str, client_id: str, websocket: WebSocket):
        await websocket.accept()
        if target_lang not in self.active_channels:
            self.active_channels[target_lang] = {}
        self.active_channels[target_lang][client_id] = websocket
        log.info(f"채널 [{target_lang}]에 클라이언트 [{client_id}] 연결. 현재 인원: {len(self.active_channels[target_lang])}명")

    def disconnect(self, target_lang: str, client_id: str):
        if target_lang in self.active_channels and client_id in self.active_channels[target_lang]:
            del self.active_channels[target_lang][client_id]
            log.info(f"채널 [{target_lang}]에서 클라이언트 [{client_id}] 연결 해제. 현재 인원: {len(self.active_channels[target_lang])}명")
            if not self.active_channels[target_lang]:
                del self.active_channels[target_lang]

    async def send_personal_json(self, target_lang: str, client_id: str, data: dict):
        """특정 클라이언트에게만 JSON 데이터를 전송합니다."""
        if target_lang in self.active_channels and client_id in self.active_channels[target_lang]:
            websocket = self.active_channels[target_lang][client_id]
            try:
                await websocket.send_text(json.dumps(data))
            except (WebSocketDisconnect, ConnectionResetError):
                log.warning(f"클라이언트 [{client_id}]에게 전송 실패 (연결 끊김).")
                self.disconnect(target_lang, client_id)

    async def broadcast_json(self, target_lang: str, data: dict):
        """해당 채널의 모든 클라이언트에게 JSON 데이터를 텍스트로 방송합니다."""
        if target_lang not in self.active_channels:
            return
        
        json_string = json.dumps(data)
        # 동시 전송을 위해 코루틴 리스트 생성
        disconnected_clients = []
        for client_id, connection in self.active_channels[target_lang].items():
            try:
                await connection.send_text(json_string)
            except (WebSocketDisconnect, ConnectionResetError):
                log.warning(f"채널 [{target_lang}]의 클라이언트 [{client_id}]에게 방송 실패 (연결 끊김).")
                disconnected_clients.append(client_id)
        
        # 연결이 끊긴 클라이언트 정리
        for client_id in disconnected_clients:
            self.disconnect(target_lang, client_id)

manager = ConnectionManager()
