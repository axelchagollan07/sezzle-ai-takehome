import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiClient:
    """Minimal Gemini client used by the Sezzle support agent."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        if not model:
            raise RuntimeError("GEMINI_MODEL is not configured.")

        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """Generate a text response from the configured Gemini model."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text


if __name__ == "__main__":
    llm = GeminiClient()

    response = llm.generate(
        "Respond with exactly: Sezzle AI assistant connection successful."
    )

    print(response)