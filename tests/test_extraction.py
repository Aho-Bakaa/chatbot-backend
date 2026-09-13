"""Unit tests for the extraction pipeline and its JSON fallback path."""

from app.services.extraction import run_extraction, _line_split_fallback


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def generate(self, prompt):
        reply = self.replies[self.calls]
        self.calls += 1
        return reply


def test_valid_json_parsed_without_fallback():
    client = FakeClient([
        '["voltage gain", "input impedance", "frequency response"]',
        '["What is voltage gain?", "What is input impedance?"]',
    ])
    result = run_extraction(client, "Study the common-emitter amplifier.", 3, 2)
    assert result["phrases"] == ["voltage gain", "input impedance", "frequency response"]
    assert result["questions"] == ["What is voltage gain?", "What is input impedance?"]
    assert result["phrases_fallback"] is False
    assert result["questions_fallback"] is False


def test_malformed_json_triggers_line_split_fallback():
    malformed = (
        "Sure, here are the phrases:\n"
        "1. voltage gain\n"
        "2. input impedance\n"
        "3. - frequency response"
    )
    client = FakeClient([malformed, "```\n- What is voltage gain?\n- What is impedance?\n```"])
    result = run_extraction(client, "Study the common-emitter amplifier.", 3, 2)
    assert result["phrases_fallback"] is True
    assert result["questions_fallback"] is True
    assert result["phrases"] == ["voltage gain", "input impedance", "frequency response"]
    assert result["questions"] == ["What is voltage gain?", "What is impedance?"]


def test_line_split_strips_markdown_and_numbering():
    raw = "```json\n[\"a\", \"b\"]\n```\n- item one\n2. item two"
    cleaned = _line_split_fallback(raw)
    assert "a" not in cleaned
    assert "json" not in " ".join(cleaned).lower()
    assert cleaned == ["item one", "item two"]


def test_json_wrapped_in_prose_is_still_parsed():
    client = FakeClient([
        'Here you go: ["gain", "impedance"] hope this helps!',
        '["q1", "q2"]',
    ])
    result = run_extraction(client, "Study the amplifier.", 2, 1)
    assert result["phrases_fallback"] is False
    assert result["phrases"] == ["gain", "impedance"]
