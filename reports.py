from models import Review, evidence_coverage


def report_text(review: Review, metadata: dict, refinements: dict) -> str:
    lines = [
        "Resume review", "", f"Generated: {metadata['generated_at']}",
        f"Provider: {metadata['provider']} | Model: {metadata['model']}",
        f"Few-shot examples: {'enabled' if metadata['use_examples'] else 'disabled'}",
        "", "Summary", review.summary, "",
        f"Requirement coverage: {evidence_coverage(review)}%",
        "Coverage describes the evidence found, not an ATS score or a hiring prediction.",
        "Weights: Required = 2, Preferred = 1. Credit: Supported = 1, Partial = 0.5, Not shown = 0.",
        "", "Requirements",
    ]
    for item in review.requirements:
        lines.extend([f"\n{item.requirement} | {item.importance} | {item.status}",
                      f"Job evidence: {item.job_evidence}",
                      f"Resume evidence: {item.resume_evidence or '(not shown)'}",
                      f"Next step: {item.advice}"])
    lines.extend(["", "Improvements"])
    lines.extend(f"{i}. {text}" for i, text in enumerate(review.priorities, 1))
    lines.extend(["", "Bullet suggestions"])
    for index, bullet in enumerate(review.bullet_rewrites):
        lines.extend([f"\n{index + 1}. Original: {bullet.original}",
                      f"First draft: {bullet.improved}", f"Why: {bullet.explanation}"])
        for version, edit in enumerate(refinements.get(index, []), 1):
            lines.extend([f"Revision {version}: {edit['improved']}",
                          f"Preference: {edit['feedback']}", f"Why: {edit['explanation']}",
                          f"Generated with: {edit['provider']} / {edit['model']}"])
    lines.extend(["", "Review all suggested wording for factual accuracy before using it."])
    return "\n".join(lines)
