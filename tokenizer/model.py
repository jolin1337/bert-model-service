from tokenizer.tokenizer_methods import bv_tokenize, load_models


class Model:
    def __init__(self):
        print("Inistialize tokenizer model...")
        self.models = load_models()

    def predict(self, text):
        return bv_tokenize(text.split())


_model = Model()


def get_model():
    return _model


if __name__ == '__main__':
    model = get_model()
    print(model.predict('Den här meningen går att delaupp med hjälp av massuppdelning!'))
