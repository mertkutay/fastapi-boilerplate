from humps import camelize
from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
