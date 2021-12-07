import json

import torch
from transformers import AutoTokenizer, BertForTokenClassification, pipeline

with open("part_of_speech/config.json") as json_file:
    config = json.load(json_file)


class Model:
    def __init__(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print("Inistialize POS model...")
        self.tokenizer = AutoTokenizer.from_pretrained(config['BERT_TOKENIZER'], cache_dir=config["PRE_TRAINED_TOKENIZER"])
        self._model = BertForTokenClassification.from_pretrained(config["BERT_MODEL"], cache_dir=config["PRE_TRAINED_MODEL"])

        self.pipeline = pipeline(
            'ner',
            tokenizer=self.tokenizer,
            model=self._model,
        )
        self._model.to(self.device)

    def predict(self, text):
        return self.pipeline(text)


_model = None


def get_model():
    global _model
    if _model is None:
        _model = Model()
    return _model


if __name__ == '__main__':
    model = get_model()
    print("Test prediction:", model.predict('This app is a total waste of time!'))
