# queues.py
#from multiprocessing import Queue
from queue import Queue

# 1) WebSocket → STT 입력
stt_input_queue   = Queue()

# 2) STT → 텍스트 결과 (번역 코루틴이 이 큐를 읽음)
stt_output_queue  = Queue()

# 3) 번역 → TTS 입력
tts_input_queue   = Queue()

# 4) TTS → WS 응답
tts_output_queue = Queue()
