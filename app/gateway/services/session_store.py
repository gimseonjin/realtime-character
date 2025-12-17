from collections import defaultdict, deque


class SessionStore:
    def __init__(self, max_turns: int = 10):
        self._hist = defaultdict(lambda: deque(maxlen=max_turns * 2))

    def append_user(self, session_id: str, text: str):
        self._hist[session_id].append({"role": "user", "text": text})

    def append_assistant(self, session_id: str, text: str):
        self._hist[session_id].append({"role": "assistant", "text": text})

    def get_history(self, session_id: str):
        return list(self._hist[session_id])
