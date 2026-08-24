from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from app.services.validation_service import ValidationService

router = APIRouter(
    prefix="/validation",
    tags=["Validation"]
)


class ValidationRequest(BaseModel):
    extracted_data: Dict[str, Any]


@router.post("/validate")
async def validate_request(request: ValidationRequest):

    service = ValidationService()

    result = service.validate(
        request.extracted_data
    )

    return result