from typing import Any, Dict

from .deterministic_validator import deterministic_validate
from .validation_agent import ValidationAgent


class ValidationService:

    def __init__(self):
        self.agent = ValidationAgent()

    def validate(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:

        # ---------------------------------------
        # STEP 1: Deterministic validation
        # ---------------------------------------

        deterministic_result = deterministic_validate(
            extracted_data
        )

        # ---------------------------------------
        # STEP 2: Agentic contextual validation
        # ---------------------------------------

        agent_result = self.agent.validate(
            extracted_data=extracted_data,
            deterministic_result=deterministic_result,
        )

        # ---------------------------------------
        # STEP 3: Final decision
        # ---------------------------------------

        if not deterministic_result["valid"]:

            final_status = "INCOMPLETE"

        elif agent_result.get("human_review_required"):

            final_status = "HUMAN_REVIEW"

        elif (
            agent_result.get("contextually_complete")
            and agent_result.get("consistency_check") == "PASS"
        ):

            final_status = "COMPLETE"

        else:

            final_status = "INCOMPLETE"

        return {
            "status": final_status,

            "deterministic_validation": deterministic_result,

            "agent_validation": agent_result,

            "summary": {
                "required_fields_valid":
                    deterministic_result["valid"],

                "contextually_complete":
                    agent_result.get(
                        "contextually_complete",
                        False
                    ),

                "consistency_check":
                    agent_result.get(
                        "consistency_check",
                        "WARNING"
                    ),

                "human_review_required":
                    agent_result.get(
                        "human_review_required",
                        True
                    ),
            },
        }