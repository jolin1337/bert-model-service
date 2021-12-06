import json

import torch
from transformers import AutoTokenizer, BertForTokenClassification, pipeline

with open("named_entity_recognition/config.json") as json_file:
    config = json.load(json_file)


class Model:
    def __init__(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print("Inistialize NER model...")
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


_model = Model()


def get_model():
    return _model


if __name__ == '__main__':
    model = get_model()
    print(model.predict('Obama bor i vita huset, han kommer flytta därifrån om tre dagar'))
