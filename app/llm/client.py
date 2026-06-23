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
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider.")
            self.openai_client = AsyncOpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider.")
            self.anthropic_client = AsyncAnthropic(api_key=self.api_key)
        elif self.provider == "mock":
            pass
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def get_review(self, prompt: str, system_instruction: str = "") -> str:
        """
        Queries the configured LLM provider and returns the raw response string.
        """
        if self.provider == "openai":
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"} if "json" in prompt.lower() or "json" in system_instruction.lower() else None,
                temperature=0.2
            )
            return response.choices[0].message.content or ""
            
        elif self.provider == "anthropic":
            messages = [{"role": "user", "content": prompt}]
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
            # Return a valid mock review JSON structure for testing
            mock_data = {
                "summary": "The PR changes look clean and well-structured. Key concerns: none.",
                "comments": [
                    {
                        "path": "app/config.py",
                        "line": 10,
                        "comment": "Mock review: Consider adding comments to separate configuration groups."
                    }
                ]
            }
            return json.dumps(mock_data)
            
        raise ValueError(f"Unsupported LLM provider: {self.provider}")
