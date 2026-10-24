from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def resume():
    return (ROOT / "samples/resume.txt").read_text(encoding="utf-8")


@pytest.fixture
def job():
    return (ROOT / "samples/job_description.txt").read_text(encoding="utf-8")


@pytest.fixture
def review_data():
    return {
        "summary": "The resume shows React experience. Automated testing is not shown, and Git collaboration needs more detail.",
        "requirements": [
            {"requirement": "React interfaces", "importance": "Required", "status": "Supported",
             "job_evidence": "Experience building user interfaces with React and JavaScript.",
             "resume_evidence": "Built a React interface for browsing a restaurant menu and adding items to a cart.",
             "advice": "Describe the specific React components you built."},
            {"requirement": "Automated testing", "importance": "Preferred", "status": "Not shown",
             "job_evidence": "Experience writing automated tests for web applications.",
             "resume_evidence": "", "advice": "Add testing experience only if you have it."},
            {"requirement": "Git collaboration", "importance": "Required", "status": "Partial",
             "job_evidence": "Experience using Git to collaborate on a team project.",
             "resume_evidence": "used Git to share code.",
             "advice": "Describe your role in collaboration and code review if applicable."},
        ],
        "priorities": ["Clarify your contribution to the React interface.",
                       "Explain how you collaborated with Git.", "Add real testing experience if available."],
        "bullet_rewrites": [{
            "original": "Built a React interface for browsing a restaurant menu and adding items to a cart.",
            "improved": "Developed a React interface for menu browsing and adding items to a cart.",
            "explanation": "Makes the task clearer without adding experience.",
        }],
    }
