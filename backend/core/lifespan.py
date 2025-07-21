import asyncio
import logging
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI

from backend.core.broadcaster import broadcast
from backend.workers.stt import stt_worker
from backend.workers.translate import translate_text
from backend.workers.tts import tts_worker

executor = ThreadPoolExecutor(max_workers=4)

log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()

    log.info("[LIFESPAN] stt_worker 스레드 시작")
    loop.run_in_executor(executor, stt_worker)

    log.info("[LIFESPAN] tts_worker 스레드 시작")
    loop.run_in_executor(executor, tts_worker)

    log.info("[LIFESPAN] translate_text 코루틴 시작")
    asyncio.create_task(translate_text())

    log.info("[LIFESPAN] broadcast 코루틴 시작")
    asyncio.create_task(broadcast())

    yield
    executor.shutdown(wait=False)
    log.info("[LIFESPAN] shutdown 완료")

