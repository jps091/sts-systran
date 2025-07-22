import asyncio
import logging
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI

from backend.core.broadcaster import broadcast
from backend.workers.stt import stt_worker
from backend.workers.translate import translate_worker
from backend.workers.tts import tts_worker

# CPU-bound 작업을 위한 Executor. 워커 내부의 run_in_executor에서 사용됩니다.
executor = ThreadPoolExecutor(max_workers=4)

log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI의 이벤트 루프를 가져와서 executor를 설정합니다.
    loop = asyncio.get_running_loop()
    loop.set_default_executor(executor)

    log.info("[LIFESPAN] stt_worker 태스크 시작")
    asyncio.create_task(stt_worker())

    log.info("[LIFESPAN] tts_worker 태스크 시작")
    asyncio.create_task(tts_worker())

    log.info("[LIFESPAN] translate_text 태스크 시작")
    asyncio.create_task(translate_worker())

    log.info("[LIFESPAN] broadcast 태스크 시작")
    asyncio.create_task(broadcast())

    yield

    # 애플리케이션 종료 시 executor를 안전하게 종료합니다.
    executor.shutdown(wait=True)
    log.info("[LIFESPAN] shutdown 완료")

