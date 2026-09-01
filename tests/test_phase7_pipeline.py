import json
from pathlib import Path


def test_rocketride_pipeline_uses_chat_source_for_structured_questions() -> None:
    pipeline_path = Path(__file__).resolve().parents[1] / "pipelines" / "lease_extraction.pipe"
    pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))
    components = {component["id"]: component for component in pipeline["components"]}

    assert pipeline["source"] == "chat_1"
    assert components["chat_1"]["provider"] == "chat"
    assert components["llm_gemini_1"]["input"] == [{"lane": "questions", "from": "chat_1"}]
    assert components["response_answers_1"]["input"] == [{"lane": "answers", "from": "llm_gemini_1"}]
