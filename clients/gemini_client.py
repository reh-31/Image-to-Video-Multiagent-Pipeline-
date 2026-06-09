"""Gemini client using google-genai SDK."""
from __future__ import annotations

import json
import os
import re
import time
from typing import Type, TypeVar

from dotenv import load_dotenv

load_dotenv()

import google.genai as genai  # noqa: E402  (avoids 'google' namespace shadowing)
from google.genai import types  # noqa: E402

_MODEL = "models/gemini-3.1-flash-lite"
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

T = TypeVar("T", bound=__import__("pydantic").BaseModel)
_MAX_RETRIES = 5


def _call_with_retry(fn, *args, **kwargs):
    """Retry *fn* on 429 rate-limit errors using the suggested delay."""
    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                m = re.search(r"retry in (\d+)", msg)
                wait = int(m.group(1)) if m else 60
                print(f"[Gemini] Rate limited — retrying in {wait}s (attempt {attempt + 1}/{_MAX_RETRIES})")
                time.sleep(wait)
                last_exc = exc
            elif "503" in msg or "UNAVAILABLE" in msg:
                wait = min(15 * (2 ** attempt), 120)  # 15, 30, 60, 120, 120
                print(f"[Gemini] Model unavailable — retrying in {wait}s (attempt {attempt + 1}/{_MAX_RETRIES})")
                time.sleep(wait)
                last_exc = exc
            else:
                raise
    raise last_exc


def _schema_template(schema: Type[T]) -> str:
    """Recursively build a concrete example JSON so nested models are fully shown."""
    import typing

    def _example(annotation) -> object:
        if annotation is None:
            return None
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())
        # list / List[X]
        if origin is list:
            inner = args[0] if args else str
            return [_example(inner)]
        # Optional[X] == Union[X, None]
        if origin is getattr(typing, "Union", None):
            non_none = [a for a in args if a is not type(None)]
            return _example(non_none[0]) if non_none else None
        # nested Pydantic model
        if hasattr(annotation, "model_fields"):
            return {k: _example(f.annotation) for k, f in annotation.model_fields.items()}
        # primitives
        name = getattr(annotation, "__name__", "value")
        if annotation is int:
            return 0
        if annotation is float:
            return 0.0
        if annotation is bool:
            return True
        return f"<{name}>"

    result = {k: _example(f.annotation) for k, f in schema.model_fields.items()}
    return json.dumps(result, indent=2)


def generate_structured(prompt: str, schema: Type[T], model: str = _MODEL) -> T:
    """Call Gemini with a JSON-only instruction and parse into *schema*."""
    full_prompt = (
        f"{prompt}\n\n"
        f"Return ONLY a valid JSON object with exactly these keys filled in with real values:\n"
        f"{_schema_template(schema)}\n\n"
        "Replace every placeholder with an actual value. "
        "No markdown, no backticks, no explanation. JSON only."
    )
    response = _call_with_retry(
        _client.models.generate_content, model=model, contents=full_prompt
    )
    return schema(**json.loads(strip_json_response(response.text)))


def generate_vision(image, prompt: str, schema: Type[T], model: str = _MODEL) -> T:
    """Analyse a PIL image with Gemini vision and parse the response into *schema*."""
    full_prompt = (
        f"{prompt}\n\n"
        f"Return ONLY a valid JSON object with exactly these keys filled in with real values:\n"
        f"{_schema_template(schema)}\n\n"
        "Replace every placeholder with an actual value. "
        "No markdown, no backticks, no explanation. JSON only."
    )
    response = _call_with_retry(
        _client.models.generate_content, model=model, contents=[full_prompt, image]
    )
    return schema(**json.loads(strip_json_response(response.text)))


def generate_text(prompt: str, model: str = _MODEL) -> str:
    """Call Gemini and return the raw text response."""
    response = _call_with_retry(
        _client.models.generate_content, model=model, contents=prompt
    )
    return response.text


def strip_json_response(text: str) -> str:
    """Remove markdown code fences that Gemini sometimes adds."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].strip()
    return text.strip()
