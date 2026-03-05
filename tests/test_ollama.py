import pytest
from bat_symphony.ollama import OllamaClient


@pytest.mark.asyncio
async def test_list_models():
    client = OllamaClient(base_url="http://localhost:11434")
    models = await client.list_models()
    assert isinstance(models, list)
    assert len(models) > 0
    assert any("qwen" in m["name"] for m in models)
    await client.close()


@pytest.mark.asyncio
async def test_chat_simple():
    client = OllamaClient(base_url="http://localhost:11434")
    response = await client.chat(
        model="qwen3.5:9b",
        messages=[{"role": "user", "content": "Say exactly: OLLAMA_OK"}],
        max_tokens=200,
    )
    # qwen3.5 uses thinking tokens; check content or thinking field
    combined = response["content"] + response.get("thinking", "")
    assert len(combined) > 0, "Expected non-empty response from Ollama"
    await client.close()
