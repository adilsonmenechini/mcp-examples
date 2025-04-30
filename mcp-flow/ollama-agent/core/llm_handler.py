from ollama import AsyncClient
from typing import AsyncGenerator, List


class LLM_Agent:
    def __init__(
        self, model_name: str = "gemma3:1b", host: str = "http://localhost:11434"
    ):
        self.client = AsyncClient(host=host)
        self.model_name = model_name

    async def generate(self, prompt: str, max_tokens: int = 100) -> str:
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return response.message.content
        except Exception as e:
            raise Exception(f"Generation failed: {str(e)}")

    async def generate_stream(
        self, prompt: str, max_tokens: int = 100
    ) -> AsyncGenerator[str, None]:
        try:
            async for part in await self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=max_tokens,
            ):
                yield part.message.content
        except Exception as e:
            raise Exception(f"Stream generation failed: {str(e)}")

    async def list_models(self) -> List[str]:
        try:
            models = await self.client.list()
            return [model.name for model in models]
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")

    async def close(self) -> None:
        # Cleanup if needed
        pass
