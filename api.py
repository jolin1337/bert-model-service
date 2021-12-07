from app import app
from named_entity_recognition import api as ner_api
from named_entity_recognition import get_model as get_ner_model
from part_of_speech import api as pos_api
from part_of_speech import get_model as get_pos_model
from tokenizer import api as tok_api
from tokenizer import get_model as get_tok_model

get_ner_model()
get_pos_model()
get_tok_model()
