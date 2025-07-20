from dataclasses import dataclass

@dataclass
class StsResponse:
    client_id: str
    target_lang: str
    translated_text: str
    audio_bytes: bytes