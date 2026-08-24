from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


try:
    from ..config import GROQ_API_KEY, GROQ_MODEL
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    )


GROQ_URL = (
    "https://api.groq.com/openai/v1/chat/completions"
)


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text: str) -> dict[str, Any]:

    text = (text or "").strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    ).strip()

    try:
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:

        try:
            result = json.loads(
                text[start:end + 1]
            )

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Critic agent returned invalid JSON."
    )


# ============================================================
# DETERMINISTIC CRITIC FALLBACK
# ============================================================

def _fallback_critic(
    validation_result: dict[str, Any],
) -> dict[str, Any]:

    issues: list[str] = []

    required_keys = [
        "contextually_complete",
        "consistency_check",
        "missing_context",
        "inconsistencies",
        "documentation_needed",
        "reasoning",
        "human_review_required",
        "confidence",
    ]

    missing_keys = [
        key
        for key in required_keys
        if key not in validation_result
    ]

    if missing_keys:

        issues.append(
            "Validation agent omitted required output fields: "
            + ", ".join(missing_keys)
        )

    missing_context = validation_result.get(
        "missing_context",
        [],
    )

    inconsistencies = validation_result.get(
        "inconsistencies",
        [],
    )

    documentation_needed = validation_result.get(
        "documentation_needed",
        [],
    )

    consistency = str(
        validation_result.get(
            "consistency_check",
            "",
        )
    ).upper()

    complete = validation_result.get(
        "contextually_complete"
    )

    human_review = validation_result.get(
        "human_review_required"
    )

    confidence = validation_result.get(
        "confidence"
    )

    if not isinstance(
        missing_context,
        list,
    ):
        issues.append(
            "missing_context must be a list."
        )

    if not isinstance(
        inconsistencies,
        list,
    ):
        issues.append(
            "inconsistencies must be a list."
        )

    if not isinstance(
        documentation_needed,
        list,
    ):
        issues.append(
            "documentation_needed must be a list."
        )

    if consistency not in {
        "PASS",
        "WARNING",
        "ERROR",
    }:
        issues.append(
            "Invalid consistency_check value."
        )

    if not isinstance(
        complete,
        bool,
    ):
        issues.append(
            "contextually_complete must be boolean."
        )

    if not isinstance(
        human_review,
        bool,
    ):
        issues.append(
            "human_review_required must be boolean."
        )

    try:
        confidence_value = float(
            confidence
        )

        if not 0 <= confidence_value <= 1:
            issues.append(
                "confidence must be between 0 and 1."
            )

    except (
        TypeError,
        ValueError,
    ):

        issues.append(
            "confidence must be numeric."
        )

    # --------------------------------------------------------
    # Logical consistency checks
    # --------------------------------------------------------

    if (
        complete is True
        and missing_context
    ):

        issues.append(
            "Agent marked the request complete "
            "while also reporting missing context."
        )

    if (
        consistency == "PASS"
        and inconsistencies
    ):

        issues.append(
            "Agent returned PASS consistency "
            "while reporting inconsistencies."
        )

    if (
        not human_review
        and (
            missing_context
            or inconsistencies
            or documentation_needed
        )
    ):

        issues.append(
            "Agent did not request human review "
            "despite reporting validation findings."
        )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Missing clinical context does NOT mean that the
    # validation agent failed.
    #
    # The critic checks whether the agent correctly
    # identified that missing context.
    # --------------------------------------------------------

    if missing_keys:
        status = "ERROR"
        agent_working = False
        score = 0.20

    elif issues:
        status = "WARNING"
        agent_working = True
        score = 0.65

    else:
        status = "PASS"
        agent_working = True
        score = 0.95

    return {
        "status": status,
        "agent_working": agent_working,
        "score": score,
        "issues": issues,
        "reasoning": (
            "The critic checked the validation agent's "
            "output structure and logical consistency."
        ),
        "mode": "fallback",
    }


# ============================================================
# GROQ CRITIC
# ============================================================

def _call_groq_critic(
    features: dict[str, Any],
    validation_result: dict[str, Any],
    document_text: str = "",
) -> dict[str, Any]:

    if not GROQ_API_KEY:

        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    context = {
        "request_features": features,
        "document_text": (
            document_text or ""
        )[:20000],
        "validation_agent_output": (
            validation_result
        ),
    }

    system_prompt = """
You are a critic agent in a prior-authorization AI pipeline.

Another AI agent has already performed contextual validation.

Your job is NOT to approve or deny the authorization.

Your job is to determine whether the FIRST validation
agent is functioning correctly.

Check:

1. Does the validation agent return all expected fields?
2. Are the field types reasonable?
3. Is the validation result logically consistent?
4. Are the missing-context findings actually supported
   by the supplied request/document information?
5. Did the validation agent invent unsupported patient facts?
6. Does the human_review_required flag agree with the findings?
7. Does contextually_complete agree with missing_context?
8. Does consistency_check agree with inconsistencies?

IMPORTANT:

A request having missing clinical context does NOT mean
the validation agent failed.

For example:

contextually_complete = false
missing_context = ["neurologic examination"]

can be a CORRECT validation result if the supplied
request does not contain a neurologic examination.

The critic is checking the QUALITY OF THE AGENT OUTPUT,
not whether the patient has complete documentation.

Do not approve or deny treatment.

Return ONLY JSON:

{
  "status": "PASS",
  "agent_working": true,
  "score": 0.95,
  "issues": [],
  "reasoning": "The validation agent output is structurally and logically consistent."
}

status must be:

PASS
WARNING
ERROR

agent_working must be true or false.

score must be between 0 and 1.

If the first agent output is valid but identifies
missing clinical context, return PASS or WARNING,
not ERROR.
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt.strip(),
            },
            {
                "role": "user",
                "content": (
                    "Critically review the following "
                    "validation-agent result:\n\n"
                    + json.dumps(
                        context,
                        ensure_ascii=False,
                        indent=2,
                    )
                ),
            },
        ],
        "temperature": 0.0,
        "max_tokens": 900,
    }

    request = Request(
        GROQ_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Authorization": (
                f"Bearer {GROQ_API_KEY}"
            ),
            "Content-Type": (
                "application/json"
            ),
        },
        method="POST",
    )

    try:

        with urlopen(
            request,
            timeout=45,
        ) as response:

            body = (
                response
                .read()
                .decode("utf-8")
            )

    except HTTPError as exc:

        error_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Groq critic API error "
            f"{exc.code}: "
            f"{error_body[:500]}"
        ) from exc

    except URLError as exc:

        raise RuntimeError(
            "Could not connect to Groq critic: "
            f"{exc.reason}"
        ) from exc

    data = json.loads(body)

    choices = (
        data.get("choices")
        or []
    )

    if not choices:

        raise RuntimeError(
            "Groq critic returned no choices."
        )

    content = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not content:

        raise RuntimeError(
            "Groq critic returned empty output."
        )

    result = _extract_json(
        content
    )

    return _normalise_critic(
        result
    )


# ============================================================
# NORMALIZATION
# ============================================================

def _normalise_critic(
    result: dict[str, Any],
) -> dict[str, Any]:

    status = str(
        result.get(
            "status",
            "WARNING",
        )
    ).upper()

    if status not in {
        "PASS",
        "WARNING",
        "ERROR",
    }:

        status = "WARNING"

    agent_working = result.get(
        "agent_working",
        status != "ERROR",
    )

    if not isinstance(
        agent_working,
        bool,
    ):

        agent_working = (
            status != "ERROR"
        )

    try:

        score = float(
            result.get(
                "score",
                0.0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        score = 0.0

    score = max(
        0.0,
        min(
            1.0,
            score,
        ),
    )

    issues = result.get(
        "issues",
        [],
    )

    if not isinstance(
        issues,
        list,
    ):

        issues = [str(issues)]

    return {
        "status": status,
        "agent_working": agent_working,
        "score": round(
            score,
            4,
        ),
        "issues": [
            str(issue)
            for issue in issues
            if str(issue).strip()
        ],
        "reasoning": str(
            result.get(
                "reasoning",
                "The critic reviewed the validation-agent output.",
            )
        ),
        "mode": "groq",
    }


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def run_critic_agent(
    features: dict[str, Any] | None = None,
    validation_result: dict[str, Any] | None = None,
    document_text: str = "",
) -> dict[str, Any]:

    features = features or {}
    validation_result = (
        validation_result or {}
    )

    try:

        return _call_groq_critic(
            features=features,
            validation_result=validation_result,
            document_text=document_text,
        )

    except Exception as exc:

        print(
            "[CRITIC AGENT] "
            f"Groq unavailable/error: {exc}"
        )

        result = _fallback_critic(
            validation_result
        )

        result["agent_error"] = str(
            exc
        )

        return result