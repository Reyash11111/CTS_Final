"""Compatibility facade for the contextual validation agent.

The actual Groq-backed implementation lives in ``services.validation``.
This module exposes both interfaces used by the project:
- ``run_validation_agent(...)`` used by the requests router
- ``ValidationAgent().validate(...)`` used by ValidationService/test_agent.py
"""

from __future__ import annotations

from typing import Any

from .validation import (
    run_validation_agent as _run_contextual_validation,
)


def run_validation_agent(
    features: dict[str, Any] | None = None,
    document_text: str = "",
) -> dict[str, Any]:
    """Run the contextual validation agent.

    This is intentionally a thin wrapper so every caller uses the same
    normalization, Groq call, and safe fallback implementation.
    """
    return _run_contextual_validation(
        features=features or {},
        document_text=document_text or "",
    )


class ValidationAgent:
    """Backward-compatible class interface for the validation service."""

    def validate(
        self,
        extracted_data: dict[str, Any] | None = None,
        deterministic_result: dict[str, Any] | None = None,
        document_text: str = "",
    ) -> dict[str, Any]:
        """Run contextual validation after deterministic validation.

        ``deterministic_result`` is accepted for compatibility and is not
        duplicated here because deterministic validation is already performed
        by ``ValidationService``.
        """
        features = dict(extracted_data or {})

        # Allow tests/callers to place extracted document text inside the
        # payload without requiring a separate argument.
        if not document_text:
            document_text = str(
                features.pop("_document_text", "")
                or features.pop("document_text", "")
                or ""
            )

        return run_validation_agent(
            features=features,
            document_text=document_text,
        )


# Backward-compatible aliases used by earlier experiments.
validate_request = run_validation_agent
validate_with_agent = run_validation_agent


if __name__ == "__main__":
    demo = {
        "diagnosis": "Headache",
        "diagnosis_code": "R51",
        "clinical_complaint": "Persistent headache",
        "clinical_findings": "Persistent headache; no neurologic exam documented",
        "requested_treatment": "MRI brain",
        "procedure_code": "70551",
        "treatment_type": "Diagnostic imaging",
    }

    import json

    print(json.dumps(run_validation_agent(demo), indent=2, ensure_ascii=False))
