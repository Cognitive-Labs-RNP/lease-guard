from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from rocketride import Question, RocketRideClient

load_dotenv()

PIPELINE_PATH = Path(__file__).resolve().parent.parent / "pipelines" / "lease_extraction.pipe"


def _provider_cfgs() -> tuple[tuple[str, str], ...]:
    providers = []
    if os.getenv("ROCKETRIDE_GEMINI_KEY"):
        providers.append(("gemini", "ROCKETRIDE_GEMINI_KEY"))
    if os.getenv("ROCKETRIDE_GROQ_KEY") and os.getenv("ROCKETRIDE_GROQ_BASE_URL"):
        providers.append(("groq", "ROCKETRIDE_GROQ_KEY"))
    return tuple(providers)


def _load_pipeline(*, fallback_to_groq: bool = False) -> dict[str, Any]:
    with PIPELINE_PATH.open("r", encoding="utf-8") as handle:
        pipeline = json.load(handle)

    llm_component = next(
        (component for component in pipeline.get("components", []) if component.get("id") == "llm_gemini_1"),
        None,
    )
    if llm_component is None:
        return pipeline

    if fallback_to_groq:
        llm_component["id"] = "llm_openai_api_1"
        llm_component["provider"] = "llm_openai_api"
        llm_component["config"] = {
            "profile": "custom",
            "custom": {
                "base_url": "${ROCKETRIDE_GROQ_BASE_URL}",
                "apikey": "${ROCKETRIDE_GROQ_KEY}",
                "model": "llama-3.1-8b-instant",
                "modelTotalTokens": 200000,
            },
            "parameters": {},
        }
        for item in pipeline.get("components", []):
            if item.get("id") == "response_answers_1":
                item["input"] = [{"lane": "answers", "from": "llm_openai_api_1"}]
    return pipeline


async def extract_lease(lease_text: str, *, use_groq_fallback: bool = True) -> dict[str, Any]:
    providers = _provider_cfgs()
    if not providers:
        raise RuntimeError(
            "No LLM provider keys are configured. Add ROCKETRIDE_GEMINI_KEY or ROCKETRIDE_GROQ_KEY + ROCKETRIDE_GROQ_BASE_URL to your .env file."
        )

    client = RocketRideClient()
    ordered = ["gemini", "groq"] if use_groq_fallback else ["gemini"]

    try:
        async with client:
            for provider_name in ordered:
                if provider_name == "gemini" and "gemini" not in {name for name, _ in providers}:
                    continue
                if provider_name == "groq" and "groq" not in {name for name, _ in providers}:
                    continue

                pipeline = _load_pipeline(fallback_to_groq=provider_name == "groq")
                try:
                    result = await client.use(pipeline=pipeline, source="webhook_1", name="lease_extraction")
                    response = await client.send(
                        result["token"],
                        lease_text,
                        objinfo={"name": "lease.txt"},
                        mimetype="text/plain",
                    )
                    if response.get("answers"):
                        return {
                            "provider": "llm_openai_api" if provider_name == "groq" else "llm_gemini",
                            "result": response,
                        }
                    if response.get("error"):
                        raise RuntimeError(response["error"])
                except Exception as exc:
                    if provider_name == "groq":
                        raise RuntimeError(f"Groq fallback failed: {exc}") from exc
                    continue

            raise RuntimeError("No valid Lease Extraction response was returned.")
    except RuntimeError:
        raise
    except Exception as exc:  # pragma: no cover - surfaced to caller
        raise RuntimeError(f"Lease extraction failed: {exc}") from exc


async def extract_lease_with_question(lease_text: str) -> dict[str, Any]:
    providers = _provider_cfgs()
    if not providers:
        raise RuntimeError(
            "No LLM provider keys are configured. Add ROCKETRIDE_GEMINI_KEY or ROCKETRIDE_GROQ_KEY + ROCKETRIDE_GROQ_BASE_URL to your .env file."
        )
    question = Question(expectJson=True)
    question.addQuestion(
        "Extract the material lease terms, parties, dates, rent, escalations, deadlines, obligations, and risks. "
        "Return only valid JSON with clear field names."
    )
    question.addContext(lease_text)

    provider_name, _ = providers[0]
    client = RocketRideClient()
    async with client:
        pipeline = _load_pipeline(fallback_to_groq=provider_name == "groq")
        result = await client.use(pipeline=pipeline, source="webhook_1", name="lease_extraction")
        response = await client.send(
            result["token"],
            lease_text,
            objinfo={"name": "lease.txt"},
            mimetype="text/plain",
        )
        return {"provider": "llm_openai_api" if provider_name == "groq" else "llm_gemini", "result": response}
