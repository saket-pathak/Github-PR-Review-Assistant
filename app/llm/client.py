import os
import json
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

class LLMClient:
    def __init__(self, provider: str, api_key: str = ""):
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == "openai":
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required when using openai provider.")
            self.openai_client = AsyncOpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when using anthropic provider.")
            self.anthropic_client = AsyncAnthropic(api_key=self.api_key)
        elif self.provider == "mock":
            pass
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def get_review(self, prompt: str, system_instruction: str = "") -> str:
        """
        Sends the prompt to the configured LLM and returns the text response.
        """
        if self.provider == "openai":
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            # Use gpt-4o as it is standard and supports JSON mode
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"} if "json" in prompt.lower() or "json" in system_instruction.lower() else None,
                temperature=0.2
            )
            return response.choices[0].message.content or ""
            
        elif self.provider == "anthropic":
            messages = [{"role": "user", "content": prompt}]
            
            # Use Claude 3.5 Sonnet for code reviews
            system_param = system_instruction if system_instruction else None
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.2,
                system=system_param,
                messages=messages
            )
            return response.content[0].text
            
        elif self.provider == "mock":
            # Mock review response for testing
            mock_response = {
                "summary": "This is a mock review summary. Code quality looks good overall.",
                "comments": [
                    {
                        "path": "app/api/routes.py",
                        "line": 14,
                        "comment": "Mock comment: Verify if there are any specific performance considerations here."
                    }
                ]
            }
            return json.dumps(mock_response)
            
        raise ValueError(f"Unsupported LLM provider: {self.provider}")
