import json

from pydantic import ValidationError

from models import Review, Refinement, check_numbers, validate_inputs, verify_review
from prompts import review_messages, refinement_messages
from providers import AIConfig, AIError, generate


def parse_json(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```") and clean.endswith("```"):
        lines = clean.splitlines()
        clean = "\n".join(lines[1:-1]).strip()
    result = json.loads(clean)
    if not isinstance(result, dict):
        raise ValueError("Return a single JSON object.")
    return result


def structured_result(config, messages, output_type, verifier):
    schema = output_type.model_json_schema()
    conversation = [dict(message) for message in messages]
    conversation[0]["content"] += "\nOutput JSON schema:\n" + json.dumps(schema)
    for attempt in range(2):
        raw = generate(config, conversation, schema)
        try:
            result = output_type.model_validate(parse_json(raw))
            verifier(result)
            return result
        except (ValueError, ValidationError) as error:
            if attempt:
                raise AIError("The model could not produce a valid, source-checked result after one repair. "
                              "Try shorter inputs or another model. Your last successful result is preserved.") from None
            if isinstance(error, ValidationError):
                detail = "; ".join(".".join(str(p) for p in item["loc"]) + ": " + item["msg"]
                                   for item in error.errors(include_input=False, include_url=False)[:5])
            elif isinstance(error, json.JSONDecodeError):
                detail = "The output was not valid JSON."
            else:
                detail = str(error)
            conversation.extend([
                {"role": "assistant", "content": raw[:18000]},
                {"role": "user", "content": "Repair the previous JSON response. " + detail
                 + " Follow the original task and schema. Use exact source quotations and no invented facts. "
                   "Return the complete corrected JSON object."},
            ])


def review_resume(config: AIConfig, resume: str, job: str, use_examples: bool = True) -> Review:
    validate_inputs(resume, job)
    return structured_result(config, review_messages(resume, job, use_examples), Review,
                             lambda result: verify_review(result, resume, job))


def refine_bullet(config: AIConfig, original: str, current: str, feedback: str) -> Refinement:
    if not feedback.strip():
        raise ValueError("Enter a writing preference, such as 'Make this shorter'.")
    if len(feedback) > 600:
        raise ValueError("Keep the writing preference under 600 characters.")
    return structured_result(config, refinement_messages(original, current, feedback), Refinement,
                             lambda result: check_numbers(original, result.improved))
