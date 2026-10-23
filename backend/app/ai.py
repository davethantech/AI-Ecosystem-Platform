import httpx
from fastapi import HTTPException
from .config import settings

async def generate(provider: str, model: str, system_prompt: str, prompt: str) -> tuple[str, str]:
    provider = provider.lower().strip()
    if provider == "openai":
        if not settings.openai_api_key:
            raise HTTPException(status_code=503, detail="Hosted model is not configured. Set OPENAI_API_KEY in the server environment.")
        chosen_model = model or settings.openai_model
        url = settings.openai_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {"model": chosen_model, "messages": [{"role":"system","content":system_prompt},{"role":"user","content":prompt}], "temperature":0.2}
    elif provider == "ollama":
        chosen_model = model or settings.ollama_model
        url = settings.ollama_base_url.rstrip("/") + "/api/chat"
        headers = {}
        payload = {"model":chosen_model,"stream":False,"messages":[{"role":"system","content":system_prompt},{"role":"user","content":prompt}]}
    else:
        raise HTTPException(status_code=400, detail="Unsupported model provider")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=10)) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        data = response.json()
        answer = data["message"]["content"] if provider == "ollama" else data["choices"][0]["message"]["content"]
        return answer, chosen_model
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Model provider timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Model provider returned HTTP {exc.response.status_code}") from exc
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not obtain a valid model response") from exc
