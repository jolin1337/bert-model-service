from tokenizer.tokenizer_methods import bv_tokenize, load_models


class Model:
    def __init__(self):
        print("Inistialize tokenizer model...")
        self.models = load_models()

    def predict(self, text):
        return bv_tokenize(text.split())


_model = None


def get_model():
    global _model
    if _model is None:
        _model = Model()
    return _model


if __name__ == '__main__':
    model = get_model()
    print("Test prediction:", model.predict('Den här meningen går att delaupp med hjälp av massuppdelning!'))
