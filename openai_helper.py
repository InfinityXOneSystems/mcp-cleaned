import os
from typing import List, Dict, Optional, Any

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def get_client(api_key: Optional[str] = None) -> Optional[OpenAI]:
    key = api_key or os.getenv('OPENAI_API_KEY')
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key)


def chat(messages: List[Dict[str, Any]], model: Optional[str] = None,
         system: Optional[str] = None, temperature: float = 0.7) -> Dict[str, Any]:
    client = get_client()
    if client is None:
        return {"error": "OPENAI_API_KEY not set or openai package missing"}

    msgs: List[Dict[str, Any]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages or [])

    use_model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    try:
        resp = client.chat.completions.create(
            model=use_model,
            messages=msgs,
            temperature=temperature,
        )
        choice = resp.choices[0]
        content = getattr(choice.message, 'content', None) or getattr(choice, 'text', '')
        return {
            "model": getattr(resp, 'model', use_model),
            "content": content,
            "usage": getattr(resp, 'usage', None)
        }
    except Exception as e:
        return {"error": str(e)}


def embed(texts: List[str], model: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    if client is None:
        return {"error": "OPENAI_API_KEY not set or openai package missing"}

    use_model = model or os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
    try:
        resp = client.embeddings.create(model=use_model, input=texts)
        vectors = [d.embedding for d in resp.data]
        return {"model": use_model, "vectors": vectors}
    except Exception as e:
        return {"error": str(e)}
