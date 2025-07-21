import asyncio
import logging

import aiohttp

from backend.config.settings import get_settings
from backend.schemas.request import TTSRequest
from backend.services.queues import stt_output_queue, tts_input_queue

log = logging.getLogger(__name__)
settings = get_settings()

async def _translate(
    session: aiohttp.ClientSession,
    text: str,
    #source_lang: str,
    target_lang: str,
    retries: int = 3,
    timeout: float = 5.0,
) -> str:

    #API 키 확인
    api_key = settings.google_translation_api_key
    if not api_key:
        raise ValueError("GCP_TRANSLATION_KEY가 설정되어 있지 않습니다.")

    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        "q": text,
        "target": target_lang,
        "source": "ko",
        "format": "text",
        "key": api_key,
    }

    # 재시도 로직
    for attempt in range(1, retries + 1):
        try:
            async with session.post(url, params=params, timeout=timeout) as resp:
                resp.raise_for_status()
                body = await resp.json()
                return body["data"]["translations"][0]["translatedText"]
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # 간단 백오프
            log.error(f"Google API error cause: {e}")
            await asyncio.sleep(0.5 * attempt)

    # 모두 실패하면 빈 문자열 반환
    return ""

async def translate_text():
    loop = asyncio.get_running_loop()

    # 세션 재사용으로 커넥션 오버헤드 최소화
    async with aiohttp.ClientSession() as session:
        log.warning("[Translation Manager] 시작")

        while True:
            # 멀티프로세스 큐에서 블로킹 get() 호출을 별도 스레드로 옮겨 논블로킹 처리
            client_id, target_lang, stt_text = await loop.run_in_executor(
                None,
                stt_output_queue.get
            )

            if stt_text is None:
                # 종료 시그널 받으면 루프 종료
                break

            log.warning(f"[TTS] 텍스트 수신: '''{stt_text}''' → 음성 합성 시작")
            translated = await _translate(session, stt_text, target_lang)
            log.warning(f"[Translation] {client_id=} {target_lang=} => {translated!r}")

            tts_req = TTSRequest(
                client_id=client_id,
                target_lang=target_lang,
                translated=translated
            )
            tts_input_queue.put(tts_req)

    log.warning("[Translation Manager] 종료")