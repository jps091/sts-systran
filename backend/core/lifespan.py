import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI

from backend.core.broadcaster import broadcast
from backend.workers.stt import stt_worker
from backend.workers.translate import translate_text
from backend.workers.tts import tts_worker

executor = ThreadPoolExecutor(max_workers=3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()

    print("[LIFESPAN] stt_worker 스레드 시작")
    loop.run_in_executor(executor, stt_worker)

    print("[LIFESPAN] tts_worker 스레드 시작")
    loop.run_in_executor(executor, tts_worker)

    print("[LIFESPAN] translate_text 코루틴 시작")
    asyncio.create_task(translate_text())

    print("[LIFESPAN] broadcast 코루틴 시작")
    asyncio.create_task(broadcast())

    yield
    executor.shutdown(wait=False)
    print("[LIFESPAN] shutdown 완료")

