import named_entity_recognition.api as ner_api
import part_of_speech.api as pos_api
import tokenizer.api as tok_api
from app import app
from named_entity_recognition.model import get_model as get_ner_model
from part_of_speech.model import get_model as get_pos_model
from tokenizer.model import get_model as get_tok_model

get_ner_model()
get_pos_model()
get_tok_model()
