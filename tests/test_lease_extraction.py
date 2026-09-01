import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from services.ai import extract_lease


@pytest.mark.asyncio
async def test_extract_lease_requires_provider_config() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="No LLM provider keys are configured"):
            await extract_lease("Sample lease text")


@pytest.mark.asyncio
async def test_extract_lease_returns_response_for_gemini() -> None:
    fake_result = {"token": "abc123"}
    fake_response = {"answers": ["parsed lease"]}

    with patch.dict(os.environ, {"ROCKETRIDE_GEMINI_KEY": "test-key"}, clear=True):
        with patch("services.ai.RocketRideClient") as rocketride_mock:
            mock_client = rocketride_mock.return_value
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.use = AsyncMock(return_value=fake_result)
            mock_client.chat = AsyncMock(return_value=fake_response)

            response = await extract_lease("Sample lease text")
            assert response["provider"] == "llm_gemini"
            assert response["result"]["answers"] == ["parsed lease"]
            assert mock_client.use.await_args.kwargs["source"] == "chat_1"
            assert mock_client.chat.await_args.kwargs["token"] == "abc123"


@pytest.mark.asyncio
async def test_extract_invoice_uses_a_structured_rocketride_question() -> None:
    with patch.dict(os.environ, {"ROCKETRIDE_GEMINI_KEY": "test-key"}, clear=True):
        with patch("services.ai.RocketRideClient") as rocketride_mock:
            mock_client = rocketride_mock.return_value
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.use = AsyncMock(return_value={"token": "invoice-token"})
            mock_client.chat = AsyncMock(return_value={"answers": [{"cam_expense": 1200, "rent_amount": 10000}]})

            response = await extract_lease("Invoice text", document_type="invoice")

            question = mock_client.chat.await_args.kwargs["question"]
            assert question.expectJson is True
            assert "cam_expense" in question.questions[0].text
            assert response["result"]["answers"][0]["rent_amount"] == 10000
