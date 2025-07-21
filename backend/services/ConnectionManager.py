import json
import logging
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

log = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # { "target_lang": {websocket1, websocket2, ...} } 형태
        self.active_channels: dict[str, set[WebSocket]] = {}

    async def connect(self, target_lang: str, websocket: WebSocket):
        await websocket.accept()
        if target_lang not in self.active_channels:
            self.active_channels[target_lang] = set()
        self.active_channels[target_lang].add(websocket)
        log.info(f"채널 [{target_lang}]에 새 클라이언트 연결. 현재 인원: {len(self.active_channels[target_lang])}명")

    def disconnect(self, target_lang: str, websocket: WebSocket):
        if target_lang in self.active_channels:
            self.active_channels[target_lang].remove(websocket)
            log.info(f"채널 [{target_lang}]에서 클라이언트 연결 해제. 현재 인원: {len(self.active_channels[target_lang])}명")
            if not self.active_channels[target_lang]:
                del self.active_channels[target_lang]

    # --- 💡 JSON(텍스트) 방송을 위한 새로운 함수 추가 💡 ---
    async def broadcast_json(self, target_lang: str, data: dict):
        """해당 채널의 모든 클라이언트에게 JSON 데이터를 텍스트로 방송합니다."""
        if target_lang not in self.active_channels:
            return

        json_string = json.dumps(data)  # 딕셔너리를 JSON 문자열로 변환

        # 동시에 여러 클라이언트에게 전송
        for connection in self.active_channels[target_lang]:
            try:
                # send_bytes가 아닌 send_text 사용
                await connection.send_text(json_string)
            except (WebSocketDisconnect, ConnectionResetError):
                log.warning(f"채널 [{target_lang}]의 클라이언트에게 전송 실패 (연결 끊김).")

    async def broadcast_bytes(self, target_lang: str, data: bytes):
        """해당 채널의 모든 클라이언트에게 바이트 데이터를 방송합니다."""
        if target_lang in self.active_channels:
            # 동시에 여러 클라이언트에게 전송
            for connection in self.active_channels[target_lang]:
                try:
                    await connection.send_bytes(data)
                except (WebSocketDisconnect, ConnectionResetError):
                    # 전송 중 연결이 끊어진 클라이언트는 무시하고 계속 진행
                    log.warning(f"채널 [{target_lang}]의 클라이언트에게 전송 실패 (연결 끊김).")
                    # 여기서 바로 disconnect를 호출할 수도 있음
                    # self.disconnect(target_lang, connection)

manager = ConnectionManager()