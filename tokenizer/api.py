from typing import List

from fastapi import Depends
from pydantic import BaseModel

from app import app

from .model import Model, get_model


class TextRequest(BaseModel):
    text: str


class TokensResponse(BaseModel):
    tokens: List[List[str]]


@app.post("/tokenize/predict", response_model=TokensResponse)
def predict(request: TextRequest, model: Model = Depends(get_model)):
    prediction = model.predict(request.text)
    return TokensResponse(tokens=prediction)
