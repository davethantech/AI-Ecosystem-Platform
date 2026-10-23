import pytest
from fastapi import HTTPException
from app.ai import generate
from app.config import settings

@pytest.mark.asyncio
async def test_openai_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(HTTPException) as error:
        await generate("openai", "", "system", "hello")
    assert error.value.status_code == 503
