from typing import List

from fastapi import Depends
from pydantic import BaseModel

from app import app

from .model import Model, get_model


class TextRequest(BaseModel):
    text: str


class PartOfSpeechEntityResponse(BaseModel):
    entity: str
    score: float
    index: int
    word: str
    start: int
    end: int


class PartOfSpeechResponse(BaseModel):
    tokens: List[PartOfSpeechEntityResponse]


@app.post("/part-of-speech/predict", response_model=PartOfSpeechResponse)
def predict(request: TextRequest, model: Model = Depends(get_model)):
    prediction = model.predict(request.text)
    return PartOfSpeechResponse(
        tokens=[PartOfSpeechEntityResponse(**p) for p in prediction]
    )


if __name__ == '__main__':
    get_model()
