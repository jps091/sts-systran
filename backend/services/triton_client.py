
import logging
import numpy as np
import tritonclient.http as httpclient

from backend.config.settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

def get_triton_client():
    """Triton HTTP 클라이언트를 생성하여 반환합니다."""
    try:
        client = httpclient.InferenceServerClient(
            url=settings.triton_server_url,
            verbose=False,
            ssl=False
        )
        log.info("Triton client created successfully.")
        return client
    except Exception as e:
        log.error(f"Failed to create Triton client: {e}")
        return None

def run_stt_inference(client: httpclient.InferenceServerClient, audio_chunk: bytes) -> str | None:
    """
    오디오 청크를 받아 Triton 서버로 STT 추론을 요청하고, 결과를 반환합니다.

    :param client: Triton HTTP 클라이언트
    :param audio_chunk: 16-bit PCM 오디오 데이터 (bytes)
    :return: 추론된 텍스트 또는 실패 시 None
    """
    if not client:
        log.error("Triton client is not available.")
        return None

    try:
        # 1. Bytes to NumPy object array
        audio_bytes_np = np.array([audio_chunk], dtype=np.object_)

        # 2. Prepare Triton Input with corrected name 'input__0'
        inputs = [
            httpclient.InferInput(
                "input__0",
                audio_bytes_np.shape,
                "BYTES"
            )
        ]
        inputs[0].set_data_from_numpy(audio_bytes_np, binary_data=True)
        outputs = [httpclient.InferRequestedOutput("output__0", binary_data=True)]

        # 4. Run Inference Server
        response = client.infer(
            model_name=settings.triton_model_name,
            inputs=inputs,
            outputs=outputs
        )

        # 5. Process Response
        raw_output = response.as_numpy("output__0")
        transcription = raw_output[0].decode("utf-8") if raw_output.size > 0 else ""

        return transcription

    except Exception as e:
        log.error(f"An error occurred during STT inference: {e}", exc_info=True)
        return None

# Triton 서버 상태 확인
def check_triton_server_status(client: httpclient.InferenceServerClient):
    if client:
        log.info(f"Triton server is live: {client.is_server_live()}")
        log.info(f"Triton server is ready: {client.is_server_ready()}")
