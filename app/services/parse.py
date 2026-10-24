from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError


def parse_schema[T: BaseModel](model: type[T], data: T | dict) -> T:
    try:
        if isinstance(data, model):
            return data
        return model.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc
