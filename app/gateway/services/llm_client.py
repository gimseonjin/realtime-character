import asyncio


class MockLLM:
    async def stream(self, user_text: str, history):
        # 토큰 스트리밍 "경험"을 위한 더미: 글자 단위로 흘려보냄
        reply = f"echo: {user_text}"
        for ch in reply:
            await asyncio.sleep(0.02)  # 스트리밍 느낌
            yield ch
