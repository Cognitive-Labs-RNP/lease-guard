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


async def _run_question(question: Question, *, use_groq_fallback: bool = True) -> dict[str, Any]:
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
                    result = await client.use(pipeline=pipeline, source="chat_1", name="lease_extraction")
                    response = await client.chat(token=result["token"], question=question)
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

            raise RuntimeError("RocketRide returned no usable answer.")
    except RuntimeError:
        raise
    except Exception as exc:  # pragma: no cover - surfaced to caller
        raise RuntimeError(f"RocketRide request failed: {exc}") from exc


async def extract_lease(
    document_text: str, *, document_type: str = "lease", use_groq_fallback: bool = True
) -> dict[str, Any]:
    """Extract structured lease or invoice fields through the RocketRide chat pipeline."""
    if document_type == "invoice":
        instruction = (
            "Extract invoice amounts. Return only JSON with cam_expense, rent_amount, "
            "admin_fee_amount, tax_amount, total_amount, and tenant_share_pct. Use numbers, "
            "not currency strings. If a required value is unavailable, omit it rather than guessing."
        )
    else:
        instruction = (
            "Extract lease audit terms. Return only JSON with base_rent, cam_cap_pct, "
            "tenant_share_pct, annual_increase_pct, excluded_expenses, and any supporting lease terms. "
            "Use decimals for percentages and numbers for money. Omit unknown values; do not guess."
        )
    question = Question(expectJson=True)
    question.addQuestion(instruction)
    question.addContext(document_text)
    return await _run_question(question, use_groq_fallback=use_groq_fallback)


async def generate_dispute_draft(prompt: str) -> dict[str, Any]:
    """Generate a text draft through the same RocketRide pipeline."""
    question = Question(expectJson=False)
    question.addQuestion(
        "Write a concise dispute draft based only on the supplied context. Clearly label it as a draft "
        "for human review. Do not invent lease clauses or give legal advice."
    )
    question.addContext(prompt)
    return await _run_question(question)
