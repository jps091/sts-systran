import asyncio
import logging
import wave
import io

from backend.schemas.request import STTRequest
from backend.services.queues import stt_input_queue, stt_output_queue
from backend.services.triton_client import get_triton_client, run_stt_inference, check_triton_server_status

log = logging.getLogger(__name__)

def pcm_to_wav_bytes(pcm_data: bytes) -> bytes:
    """ Raw PCM 데이터를 받아 WAV 형식의 bytes로 변환합니다. """
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm_data)
    return buffer.getvalue()

async def stt_worker():
    """
    STT 입력 큐에서 오디오 청크를 받아 처리하고, 결과를 출력 큐로 보냅니다.
    """
    log.info("STT worker starting...")

    # Triton 클라이언트 초기화
    triton_client = get_triton_client()
    if triton_client is None:
        log.error("Failed to create Triton client. STT worker cannot start.")
        return

    # Triton 서버 상태 확인
    try:
        check_triton_server_status(triton_client)
    except Exception as e:
        log.error(f"Triton server is not ready: {e}. STT worker cannot start.")
        return

    while True:
        try:
            req: STTRequest = await stt_input_queue.get()
            if req is None:
                break

            # 현재는 모든 청크에 대해 STT 추론 요청
            # TODO: 클라이언트 VAD 기반 청크로 넘겨야 효율적 작업 가능

            wav_chunk = pcm_to_wav_bytes(req.chunk)
            transcription = run_stt_inference(triton_client, wav_chunk)

            if transcription and transcription.strip():
                log.info(f"STT result for client {req.client_id}: '{transcription}'")
                await stt_output_queue.put((req.client_id, req.target_lang, transcription))

        except asyncio.CancelledError:
            log.info("STT worker cancelled.")
            break
        except Exception as e:
            log.error(f"Error in STT worker: {e}", exc_info=True)
        finally:
            stt_input_queue.task_done()

    log.info("STT worker has shut down.")
