import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.llm.client import LLMClient

def test_llm_client_init():
    # OpenAI requires API key
    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        LLMClient(provider="openai", api_key="")
        
    # Anthropic requires API key
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
        LLMClient(provider="anthropic", api_key="")
        
    # Unsupported provider
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMClient(provider="unknown", api_key="some-key")

@pytest.mark.asyncio
@patch("app.llm.client.AsyncOpenAI")
async def test_openai_provider(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    
    mock_chat = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"summary": "Looks good", "comments": []}'
    mock_chat.create.return_value = mock_response
    mock_client.chat.completions = mock_chat

    client = LLMClient(provider="openai", api_key="openai-key")
    response = await client.get_review(prompt="Review code and output json", system_instruction="System instruction")

    assert "summary" in response
    mock_chat.create.assert_called_once_with(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "Review code and output json"}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

@pytest.mark.asyncio
@patch("app.llm.client.AsyncAnthropic")
async def test_anthropic_provider(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    
    mock_messages = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = '{"summary": "Looks good", "comments": []}'
    mock_messages.create.return_value = mock_response
    mock_client.messages = mock_messages

    client = LLMClient(provider="anthropic", api_key="anthropic-key")
    response = await client.get_review(prompt="Review code", system_instruction="System instruction")

    assert "summary" in response
    mock_messages.create.assert_called_once_with(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        temperature=0.2,
        system="System instruction",
        messages=[{"role": "user", "content": "Review code"}]
    )

@pytest.mark.asyncio
async def test_mock_provider():
    client = LLMClient(provider="mock")
    response = await client.get_review(prompt="Review code")
    
    assert "Mock review" in response
