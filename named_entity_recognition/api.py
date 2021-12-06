from typing import List

from fastapi import Depends
from pydantic import BaseModel

from app import app

from .model import Model, get_model


class TextRequest(BaseModel):
    text: str


class NamedEntityRecognitionEntityResponse(BaseModel):
    entity: str
    score: float
    index: int
    word: str
    start: int
    end: int


class NamedEntityRecognitionResponse(BaseModel):
    entities: List[NamedEntityRecognitionEntityResponse]


@app.post("/named-entity-recognition/predict", response_model=NamedEntityRecognitionResponse)
def predict(request: TextRequest, model: Model = Depends(get_model)):
    prediction = model.predict(request.text)
    return NamedEntityRecognitionResponse(
        tokens=[NamedEntityRecognitionEntityResponse(**p) for p in prediction]
    )
