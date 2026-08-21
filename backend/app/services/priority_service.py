"""
Human Review Priority Service

Determines the operational priority of cases that require human review.

This does NOT make a medical diagnosis or treatment decision.
It only determines which human-review cases should be handled first.
"""

from __future__ import annotations

from typing import Any


# Priority order
PRIORITY_ORDER = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def _text(value: Any) -> str:
    """Safely convert a value to lowercase text."""
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return " ".join(str(v) for v in value).lower()

    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values()).lower()

    return str(value).lower()


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def calculate_human_review_priority(
    features: dict[str, Any] | None = None,
    agent_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate operational priority for human review.

    Priority is based on:
    1. Whether human review is actually required.
    2. Explicitly documented urgency/severity information.
    3. Presence of documented red-flag/urgent indicators.
    4. Missing critical documentation.
    5. Agent confidence and contextual completeness.

    The result is intended for workflow prioritization only.
    """

    features = features or {}
    agent_result = agent_result or {}

    # ---------------------------------------------------------
    # If no human review is needed, there is no review priority.
    # ---------------------------------------------------------
    human_review_required = bool(
        agent_result.get("human_review_required", False)
        or features.get("human_review_required", False)
    )

    if not human_review_required:
        return {
            "human_review_required": False,
            "priority": "NONE",
            "priority_score": 0,
            "severity": "NOT_APPLICABLE",
            "reason": "Human review is not currently required.",
            "priority_factors": [],
        }

    # ---------------------------------------------------------
    # Build searchable context
    # ---------------------------------------------------------
    all_text_parts = [
        _text(features.get("diagnosis")),
        _text(features.get("diagnosis_name")),
        _text(features.get("clinical_complaint")),
        _text(features.get("clinical_findings")),
        _text(features.get("medical_necessity")),
        _text(features.get("procedure")),
        _text(features.get("procedure_name")),
        _text(features.get("severity")),
        _text(features.get("urgency")),
        _text(features.get("red_flags")),
        _text(features.get("symptoms")),
        _text(features.get("document_text")),
        _text(agent_result.get("reasoning")),
        _text(agent_result.get("missing_context")),
        _text(agent_result.get("documentation_needed")),
    ]

    context = " ".join(all_text_parts)

    factors: list[str] = []
    score = 0

    # ---------------------------------------------------------
    # 1. Explicit urgency / emergency indicators
    # ---------------------------------------------------------
    critical_terms = [
        "emergency",
        "emergent",
        "life threatening",
        "life-threatening",
        "unstable",
        "critical condition",
        "acute deterioration",
        "severe deterioration",
        "urgent intervention",
        "immediate intervention",
        "stat",
        "red flag",
    ]

    if _contains_any(context, critical_terms):
        score += 60
        factors.append("Documented urgent or critical indicator")

    # ---------------------------------------------------------
    # 2. Severe symptoms / high-risk indicators
    # ---------------------------------------------------------
    high_terms = [
        "severe pain",
        "severe symptoms",
        "severe bleeding",
        "persistent bleeding",
        "high fever",
        "altered mental status",
        "loss of consciousness",
        "syncope",
        "focal neurologic deficit",
        "neurologic deficit",
        "respiratory distress",
        "shortness of breath",
        "chest pain",
        "rapid deterioration",
        "significant deterioration",
    ]

    if _contains_any(context, high_terms):
        score += 35
        factors.append("Documented severe or high-risk clinical indicator")

    # ---------------------------------------------------------
    # 3. Explicit severity values
    # ---------------------------------------------------------
    severity = _text(features.get("severity"))

    if severity:
        if _contains_any(
            severity,
            ["critical", "emergency", "emergent", "life threatening"],
        ):
            score += 60
            factors.append("Explicit critical severity documented")

        elif _contains_any(
            severity,
            ["severe", "high", "very high"],
        ):
            score += 35
            factors.append("Explicit severe/high severity documented")

        elif _contains_any(
            severity,
            ["moderate", "medium"],
        ):
            score += 20
            factors.append("Explicit moderate severity documented")

        elif _contains_any(
            severity,
            ["mild", "low"],
        ):
            score += 5
            factors.append("Explicit mild/low severity documented")

    # ---------------------------------------------------------
    # 4. Explicit urgency field
    # ---------------------------------------------------------
    urgency = _text(features.get("urgency"))

    if urgency:
        if _contains_any(
            urgency,
            ["critical", "emergency", "emergent", "immediate", "stat"],
        ):
            score += 50
            factors.append("Explicit immediate/emergency urgency documented")

        elif _contains_any(
            urgency,
            ["urgent", "high"],
        ):
            score += 30
            factors.append("Explicit urgent/high urgency documented")

        elif _contains_any(
            urgency,
            ["routine", "standard", "normal"],
        ):
            score += 5
            factors.append("Routine urgency documented")

    # ---------------------------------------------------------
    # 5. Missing context
    # ---------------------------------------------------------
    missing_context = agent_result.get("missing_context", [])

    if isinstance(missing_context, list):
        missing_count = len(missing_context)
    else:
        missing_count = 0

    if missing_count >= 6:
        score += 20
        factors.append("Multiple important contextual fields are missing")

    elif missing_count >= 3:
        score += 10
        factors.append("Several contextual fields are missing")

    elif missing_count > 0:
        score += 5
        factors.append("Some contextual information is missing")

    # ---------------------------------------------------------
    # 6. Documentation gaps
    # ---------------------------------------------------------
    documentation_needed = agent_result.get(
        "documentation_needed",
        [],
    )

    if isinstance(documentation_needed, list):
        documentation_count = len(documentation_needed)
    else:
        documentation_count = 0

    if documentation_count >= 3:
        score += 15
        factors.append("Multiple documentation gaps require reviewer attention")

    elif documentation_count > 0:
        score += 8
        factors.append("Additional documentation is required")

    # ---------------------------------------------------------
    # Cap score
    # ---------------------------------------------------------
    score = min(score, 100)

    # ---------------------------------------------------------
    # Determine operational priority
    # ---------------------------------------------------------
    if score >= 70:
        priority = "CRITICAL"
        severity_label = "CRITICAL"
        reason = (
            "Human review is required and the request contains "
            "documented urgent, severe, or high-risk indicators."
        )

    elif score >= 45:
        priority = "HIGH"
        severity_label = "HIGH"
        reason = (
            "Human review is required and the request contains "
            "significant severity, urgency, or documentation concerns."
        )

    elif score >= 20:
        priority = "MEDIUM"
        severity_label = "MODERATE"
        reason = (
            "Human review is required because contextual or "
            "documentation checks need reviewer attention."
        )

    else:
        priority = "LOW"
        severity_label = "LOW"
        reason = (
            "Human review is required, but no high-severity or "
            "urgent indicator was documented."
        )

    return {
        "human_review_required": True,
        "priority": priority,
        "priority_score": score,
        "severity": severity_label,
        "reason": reason,
        "priority_factors": factors,
    }


def priority_rank(priority: str) -> int:
    """Return numeric priority rank for sorting."""
    return PRIORITY_ORDER.get(
        str(priority).upper(),
        0,
    )