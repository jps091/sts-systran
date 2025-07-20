import logging
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.core.lifespan import lifespan
from backend.router.sts import sts_router


# --- Logging Settings ---
logging.basicConfig(
    level=logging.WARNING,
    format="(%(asctime)s) %(levelname)s - %(name)s - %(message)s",
    datefmt="%y-%m-%d %H:%M:%S"
)

# Uvicorn 기본 로거 출력抑制
logging.getLogger("uvicorn.error").propagate = False
logging.getLogger("uvicorn.access").propagate = False

# --- FastAPI App 생성 ---
app = FastAPI(
    title="Real-Time STT/Translate/TTS Service",
    description="Real-time voice translation service API",
    version="1.0.0",
    lifespan=lifespan  # → lifespan이 None이면 제거
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실운영 시 도메인 명시적으로 지정 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 라우터 등록 ---
app.include_router(sts_router)

# --- 헬스 체크 ---
@app.get("/", summary="Health Check")
async def health_check():
    """서버 정상 작동 여부 확인용 엔드포인트"""
    return "OK"

# --- 서버 실행 ---
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)