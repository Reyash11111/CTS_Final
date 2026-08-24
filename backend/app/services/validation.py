
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
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _clean_features(features: dict[str, Any] | None) -> dict[str, Any]:
    """Remove internal/private values and make the payload JSON-safe."""
    if not isinstance(features, dict):
        return {}

    cleaned: dict[str, Any] = {}

    for key, value in features.items():
        if str(key).startswith("_"):
            continue

        if key == "validation_agent":
            continue

        try:
            json.dumps(value)
            cleaned[key] = value
        except (TypeError, ValueError):
            cleaned[key] = str(value)

    return cleaned


def _extract_json(text: str) -> dict[str, Any]:
    """
    Extract the first JSON object from an LLM response.

    Handles responses wrapped in ```json ... ``` as well as plain JSON.
    """
    text = (text or "").strip()

    # Remove markdown fences if present.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Fallback: find the outermost-looking JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    raise ValueError("The validation agent returned invalid JSON.")


def _normalise_result(result: dict[str, Any]) -> dict[str, Any]:
    """Guarantee the response shape expected by the React UI."""
    missing_context = result.get("missing_context", [])
    inconsistencies = result.get("inconsistencies", [])
    documentation_needed = result.get("documentation_needed", [])

    if not isinstance(missing_context, list):
        missing_context = [str(missing_context)]

    if not isinstance(inconsistencies, list):
        inconsistencies = [str(inconsistencies)]

    if not isinstance(documentation_needed, list):
        documentation_needed = [str(documentation_needed)]

    consistency = str(
        result.get("consistency_check", "WARNING")
    ).upper()

    if consistency not in {"PASS", "WARNING", "ERROR"}:
        consistency = "WARNING"

    confidence = result.get("confidence", 0.0)

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(0.0, min(1.0, confidence))

    complete = result.get("contextually_complete")

    if not isinstance(complete, bool):
        complete = len(missing_context) == 0

    human_review = result.get("human_review_required")

    if not isinstance(human_review, bool):
        human_review = (
            not complete
            or consistency in {"WARNING", "ERROR"}
            or bool(inconsistencies)
            or bool(documentation_needed)
        )

    return {
        "contextually_complete": complete,
        "consistency_check": consistency,
        "missing_context": [str(x) for x in missing_context if str(x).strip()],
        "inconsistencies": [str(x) for x in inconsistencies if str(x).strip()],
        "documentation_needed": [
            str(x) for x in documentation_needed if str(x).strip()
        ],
        "reasoning": str(
            result.get(
                "reasoning",
                "The request was reviewed for contextual completeness and consistency.",
            )
        ),
        "human_review_required": human_review,
        "confidence": confidence,
    }


def _fallback_validation(
    features: dict[str, Any],
    document_text: str = "",
) -> dict[str, Any]:
    """
    Safe fallback when Groq is unavailable.

    This does NOT replace the LLM agent for contextual reasoning. It only
    prevents the API from crashing if the external model is unavailable.
    """

    diagnosis = str(features.get("diagnosis") or "").lower()
    treatment = str(features.get("requested_treatment") or "").lower()
    complaint = str(features.get("clinical_complaint") or "").strip()
    findings = str(features.get("clinical_findings") or "").strip()

    missing: list[str] = []
    documentation: list[str] = []
    inconsistencies: list[str] = []

    # Generic contextual checks.
    if not complaint:
        missing.append("clinical complaint or presenting symptoms")

    if not findings:
        missing.append("relevant clinical findings")

    # Procedure-specific contextual checks.
    if "mri" in treatment or "magnetic resonance" in treatment:
        if "headache" in diagnosis or "headache" in complaint.lower():
            text = f"{complaint} {findings} {document_text}".lower()

            if not any(
                term in text
                for term in (
                    "duration",
                    "days",
                    "weeks",
                    "months",
                    "persistent",
                )
            ):
                missing.append("duration of headache")

            if not any(
                term in text
                for term in (
                    "severity",
                    "severe",
                    "moderate",
                    "mild",
                    "10/10",
                )
            ):
                missing.append("characteristics/severity of headache")

            if not any(
                term in text
                for term in (
                    "neurologic exam",
                    "neurological examination",
                    "neurologic examination",
                    "neurologically intact",
                )
            ):
                missing.append("neurologic examination findings")

            if not any(
                term in text
                for term in (
                    "red flag",
                    "red flags",
                    "sudden onset",
                    "focal deficit",
                    "focal deficits",
                    "fever",
                    "vision loss",
                )
            ):
                missing.append(
                    "red flag assessment (e.g., sudden onset, focal deficits, systemic symptoms)"
                )

            if not any(
                term in text
                for term in (
                    "prior imaging",
                    "previous imaging",
                    "ct scan",
                    "previous mri",
                )
            ):
                missing.append("prior imaging studies")

            if not any(
                term in text
                for term in (
                    "medication",
                    "medications",
                    "treatment tried",
                    "previous treatment",
                    "conservative management",
                    "analgesic",
                    "therapy tried",
                )
            ):
                missing.append(
                    "details of previous treatments or medications tried"
                )

            documentation.append(
                "clinical justification for MRI brain given the documented symptoms and examination"
            )

            documentation.append(
                "record of prior conservative management or pharmacologic therapy"
            )

    complete = len(missing) == 0

    return {
        "contextually_complete": complete,
        "consistency_check": "PASS" if complete and not inconsistencies else "WARNING",
        "missing_context": missing,
        "inconsistencies": inconsistencies,
        "documentation_needed": documentation,
        "reasoning": (
            "The contextual validation fallback reviewed the submitted diagnosis, "
            "requested treatment, clinical complaint, findings, and available "
            "document text. Additional clinical context is required before the "
            "request can be considered contextually complete."
            if missing
            else
            "The available request information did not reveal missing contextual "
            "requirements during the fallback validation."
        ),
        "human_review_required": bool(missing or inconsistencies or documentation),
        "confidence": 0.60 if missing else 0.75,
    }


def _call_groq(
    features: dict[str, Any],
    document_text: str = "",
) -> dict[str, Any]:
    """Call Groq using its OpenAI-compatible HTTP API."""

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to backend/.env."
        )

    request_context = {
        "request_fields": _clean_features(features),
        "clinical_document_text": (document_text or "")[:30000],
    }

    system_prompt = """
You are a clinical prior-authorization validation agent.

Your role is NOT to approve or deny the authorization.
The deterministic engine has already checked that required fields exist.

Your job is to perform a SECONDARY contextual validation.

Check:
1. Contextual completeness:
   - Is there enough clinical context to understand why the requested treatment,
     test, imaging, or procedure is needed?
2. Consistency:
   - Does the diagnosis fit the symptoms/findings?
   - Does the requested procedure/treatment reasonably relate to the diagnosis?
   - Identify contradictions only when evidence actually supports them.
3. Missing context:
   - List specific clinical information that should be supplied.
4. Documentation needed:
   - List supporting documentation that would strengthen the request.
5. Human review:
   - Set true when missing context, meaningful inconsistency, or documentation
     gaps make automated interpretation unreliable.

IMPORTANT:
- Do not invent patient facts.
- Do not diagnose a new condition.
- Do not deny treatment.
- Do not treat a missing optional field as a deterministic validation failure.
- Be specific and clinically contextual.
- Use the supplied document text when available.
- If the information is genuinely sufficient, return an empty list for missing_context.

Return ONLY valid JSON with exactly these keys:

{
  "contextually_complete": true,
  "consistency_check": "PASS",
  "missing_context": [],
  "inconsistencies": [],
  "documentation_needed": [],
  "reasoning": "Short explanation.",
  "human_review_required": false,
  "confidence": 0.90
}

consistency_check must be one of:
PASS, WARNING, ERROR

confidence must be between 0 and 1.
"""

    user_prompt = (
        "Validate the following prior-authorization request context:\n\n"
        + json.dumps(request_context, ensure_ascii=False, indent=2)
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1200,
    }

    request = Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Groq API error {exc.code}: {error_body[:500]}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not connect to Groq: {exc.reason}"
        ) from exc

    data = json.loads(body)

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Groq returned no choices.")

    content = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not content:
        raise RuntimeError("Groq returned an empty response.")

    return _extract_json(content)


def run_validation_agent(
    features: dict[str, Any] | None = None,
    document_text: str = "",
) -> dict[str, Any]:
    """
    Public entry point used by requests.py.

    Supports BOTH calls already present in your router:

        run_validation_agent(features)

    and:

        run_validation_agent(
            features=features,
            document_text=document_text,
        )
    """

    features = features or {}

    try:
        result = _call_groq(
            features=features,
            document_text=document_text,
        )
        return _normalise_result(result)

    except Exception as exc:
        print(f"[VALIDATION AGENT] Groq unavailable/error: {exc}")

        # Keep the API alive and still provide a useful validation result.
        fallback = _fallback_validation(
            features=features,
            document_text=document_text,
        )

        fallback["agent_error"] = str(exc)
        return _normalise_result(fallback)


# Optional aliases for compatibility with earlier experiments.
validate_request = run_validation_agent
validate_with_agent = run_validation_agent


if __name__ == "__main__":
    demo_features = {
        "diagnosis": "Headache",
        "diagnosis_code": "R51",
        "clinical_complaint": "Persistent headache",
        "clinical_findings": "No neurologic examination documented",
        "requested_treatment": "MRI brain",
        "procedure_code": "70551",
        "treatment_type": "Diagnostic imaging",
    }

    result = run_validation_agent(demo_features)

    print("\n==============================")
    print("VALIDATION AGENT RESULT")
    print("==============================")
    print(json.dumps(result, indent=2, ensure_ascii=False))