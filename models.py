import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MAX_RESUME = 12000
MAX_JOB = 8000


class OutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Requirement(OutputModel):
    requirement: str = Field(min_length=1, max_length=300)
    importance: Literal["Required", "Preferred"]
    status: Literal["Supported", "Partial", "Not shown"]
    job_evidence: str = Field(min_length=1, max_length=500)
    resume_evidence: str = Field(max_length=500)
    advice: str = Field(min_length=1, max_length=600)


class BulletRewrite(OutputModel):
    original: str = Field(min_length=1, max_length=1000)
    improved: str = Field(min_length=1, max_length=1200)
    explanation: str = Field(min_length=1, max_length=600)


class Review(OutputModel):
    summary: str = Field(min_length=1, max_length=1200)
    requirements: list[Requirement] = Field(min_length=1, max_length=8)
    priorities: list[str] = Field(min_length=1, max_length=5)
    bullet_rewrites: list[BulletRewrite] = Field(min_length=1, max_length=3)


class Refinement(OutputModel):
    improved: str = Field(min_length=1, max_length=1200)
    explanation: str = Field(min_length=1, max_length=600)


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def contains_quote(source: str, quote: str) -> bool:
    return bool(quote.strip()) and normalized(quote) in normalized(source)


def check_numbers(source: str, suggested: str) -> None:
    pattern = r"(?<![\w])\d+(?:[.,]\d+)*(?:%|\+)?"
    original_numbers = set(re.findall(pattern, source))
    new_numbers = set(re.findall(pattern, suggested)) - original_numbers
    if new_numbers:
        raise ValueError("A rewritten bullet introduces a number absent from its original source.")


def validate_inputs(resume: str, job: str) -> None:
    if len(resume.strip()) < 100:
        raise ValueError("Paste at least 100 characters of resume text.")
    if len(job.strip()) < 100:
        raise ValueError("Paste at least 100 characters of the job description.")
    if len(resume) > MAX_RESUME or len(job) > MAX_JOB:
        raise ValueError(f"Keep the resume under {MAX_RESUME:,} characters and the job under {MAX_JOB:,}.")


def verify_review(review: Review, resume: str, job: str) -> None:
    seen = set()
    for requirement in review.requirements:
        key = normalized(requirement.requirement)
        if key in seen:
            raise ValueError("Duplicate requirements were returned; each requirement must be unique.")
        seen.add(key)
        if not contains_quote(job, requirement.job_evidence):
            raise ValueError("A job_evidence quotation is not present in the job description.")
        if requirement.status == "Not shown":
            if requirement.resume_evidence:
                raise ValueError("Not shown requirements must have an empty resume_evidence string.")
        elif not contains_quote(resume, requirement.resume_evidence):
            raise ValueError("A resume_evidence quotation is not present in the resume.")
    for bullet in review.bullet_rewrites:
        if not contains_quote(resume, bullet.original):
            raise ValueError("An original bullet is not present in the resume.")
        check_numbers(bullet.original, bullet.improved)


def evidence_coverage(review: Review) -> int:
    weights = {"Required": 2, "Preferred": 1}
    credit = {"Supported": 1, "Partial": 0.5, "Not shown": 0}
    total = sum(weights[item.importance] for item in review.requirements)
    earned = sum(weights[item.importance] * credit[item.status] for item in review.requirements)
    return round(100 * earned / total)
