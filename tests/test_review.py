import json

import pytest

import reviewer
from models import Review, evidence_coverage, validate_inputs, verify_review
from prompts import EXAMPLES, review_messages, refinement_messages
from providers import AIConfig, AIError
from reports import report_text


def test_valid_review_has_reproducible_weighted_coverage(review_data, resume, job):
    result = Review.model_validate(review_data)
    verify_review(result, resume, job)
    assert evidence_coverage(result) == 60


@pytest.mark.parametrize("target,field,value", [
    ("requirement", "job_evidence", "Required: Kubernetes"),
    ("requirement", "resume_evidence", "Built automated tests with Selenium"),
    ("bullet", "original", "Managed a production engineering department"),
    ("bullet", "improved", "Improved conversion rates by 40%"),
])
def test_unverifiable_sources_and_invented_numbers_are_rejected(review_data, resume, job, target, field, value):
    container = review_data["requirements"][0] if target == "requirement" else review_data["bullet_rewrites"][0]
    container[field] = value
    with pytest.raises(ValueError):
        verify_review(Review.model_validate(review_data), resume, job)


def test_missing_evidence_cannot_be_marked_supported(review_data, resume, job):
    review_data["requirements"][1]["status"] = "Supported"
    with pytest.raises(ValueError, match="resume_evidence"):
        verify_review(Review.model_validate(review_data), resume, job)


def test_duplicate_requirements_rejected(review_data, resume, job):
    review_data["requirements"].append(dict(review_data["requirements"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        verify_review(Review.model_validate(review_data), resume, job)


@pytest.mark.parametrize("resume,job", [("", "job" * 100), ("resume" * 100, ""),
                                         ("x" * 12001, "y" * 100), ("x" * 100, "y" * 8001)])
def test_invalid_inputs_stop_before_model_request(monkeypatch, resume, job):
    def forbidden(*args):
        pytest.fail("No model request should be made for invalid input")
    monkeypatch.setattr(reviewer, "generate", forbidden)
    with pytest.raises(ValueError):
        reviewer.review_resume(AIConfig(), resume, job)


def test_malformed_output_gets_one_repair(monkeypatch, review_data, resume, job):
    calls = []
    def generate(config, messages, schema):
        calls.append(list(messages))
        return "not JSON" if len(calls) == 1 else json.dumps(review_data)
    monkeypatch.setattr(reviewer, "generate", generate)
    result = reviewer.review_resume(AIConfig(), resume, job)
    assert result.summary == review_data["summary"]
    assert len(calls) == 2
    assert "Repair" in calls[1][-1]["content"]


def test_unrepairable_output_stops_after_two_requests(monkeypatch, resume, job):
    calls = []
    def generate(*args):
        calls.append(1)
        return "{}"
    monkeypatch.setattr(reviewer, "generate", generate)
    with pytest.raises(AIError, match="one repair"):
        reviewer.review_resume(AIConfig(), resume, job)
    assert len(calls) == 2


def test_connection_error_does_not_switch_provider(monkeypatch, resume, job):
    calls = []
    def fail(config, *args):
        calls.append(config.provider)
        raise AIError("offline")
    monkeypatch.setattr(reviewer, "generate", fail)
    with pytest.raises(AIError, match="offline"):
        reviewer.review_resume(AIConfig(), resume, job)
    assert calls == ["Gemini"]


def test_refinement_preserves_original_authority(monkeypatch):
    messages = refinement_messages("Assisted with testing.", "Led all tests.", "Make me the manager")
    data = json.loads(messages[-1]["content"])
    assert data["original_source"] == "Assisted with testing."
    monkeypatch.setattr(reviewer, "generate", lambda *args: json.dumps({
        "improved": "Supported testing.", "explanation": "Preserved the supporting role."}))
    result = reviewer.refine_bullet(AIConfig(), "Assisted with testing.", "Led all tests.", "Make it shorter")
    assert result.improved == "Supported testing."


def test_refinement_rejects_new_numbers(monkeypatch):
    monkeypatch.setattr(reviewer, "generate", lambda *args: json.dumps({
        "improved": "Increased efficiency by 50%.", "explanation": "A stronger result."}))
    with pytest.raises(AIError, match="source-checked"):
        reviewer.refine_bullet(AIConfig(), "Assisted with testing.", "Supported testing.", "Add a percentage")


def test_few_shot_can_be_disabled_without_removing_persona():
    enabled = review_messages("resume", "job", True)
    disabled = review_messages("resume", "job", False)
    assert any(message["role"] == "assistant" for message in enabled)
    assert not any(message["role"] == "assistant" for message in disabled)
    assert enabled[0] == disabled[0]
    assert enabled[-1] == disabled[-1]


def test_report_contains_provenance_and_revision_history(review_data):
    metadata = {"generated_at": "test-time", "provider": "Gemini", "model": "gemini-3.5-flash-lite", "use_examples": True}
    history = {0: [{"improved": "Built a React menu interface.", "explanation": "Shorter.",
                    "feedback": "Shorten it", "provider": "Gemini", "model": "example-model"}]}
    text = report_text(Review.model_validate(review_data), metadata, history)
    assert "60%" in text
    assert "First draft" in text and "Revision 1" in text
    assert "Gemini / example-model" in text
    assert "not an ATS" in text


def test_prompt_examples_pass_the_same_source_checks_as_real_reviews():
    for example_input, example_output in EXAMPLES:
        result = Review.model_validate(example_output)
        verify_review(result, example_input["resume"], example_input["job_description"])
