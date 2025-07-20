from dataclasses import dataclass

from pydantic import BaseModel


class AudioRequest(BaseModel):
    target_lang: str  # "en" or "es"
    client_id: str

@dataclass
class STTRequest:
    client_id: str
    target_lang: str
    chunk: bytes

@dataclass
class TTSRequest:
    client_id: str
    target_lang: str
    translated: str