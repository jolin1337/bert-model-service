# Deploy BERT for Sentiment Analsysi with FastAPI

Deploy a pre-trained BERT model for Sentiment Analysis as a REST API using FastAPI

## Demo

The API currently support NER and POS tagging as well as a generalized tokenizer model that splits words that Swedish languages usually concatenates together. The models are loaded from the KB/Bert repository at huggingface website: [](https://huggingface.co/KB).

### Tokenizer
This model combines opus, kb-bert and af models to tokenize the input text and outputs a list of lists of tokens where each item in the outer list corresponds to the text string separated by a space character. The inner list contains all words the tokenizer model has devided the word into. This model should be combined with POS and NER models to reduce vocabulary.

Here's a sample request to the API (note: installation of http-test library can be done on any linux computer by `apt-get install httpie`):

```bash
http POST http://127.0.0.1:8081/tokenize/predict text="Obama bor i vitahuset, han kommer flytta därifrån om tre dagar"
```

The response you'll get looks something like this:

```js
{
    "tokens": [
        ["Obama"],
        ["bor"],
        ["i"],
        ["vita", "huset", ","],
        ["han"],
        ["kommer"],
        ["flytta"],
        ["där", "ifrån"],
        ["om"],
        ["tre"],
        ["dagar"],
    ]
}
```

### Part-of-Speech

This model downloads and uses `KB/bert-base-swedish-cased-pos` model to tag each word in the input text with a part-of-speech tag.

Here's a sample request to the API (note: installation of http-test library can be done on any linux computer by `apt-get install httpie`):

```bash
http POST http://127.0.0.1:8081/part-of-speech/predict text="Obama bor i vitahuset, han kommer flytta därifrån om tre dagar"
```

The response you'll get looks something like this:

```js
{
    "tokens": [
        { "word": "Obama", "start": 0, "end": 4, "entity": "NN", "score": 0.9987 },
        ....
        { "word": "dagar"...}
    ]
}
```

### Named-Entity-Recognition

This model downloads and uses `KB/bert-base-swedish-cased-ner` model to tag all words in the input text that has a potential named entity. The entiteis the model considers are: `Name (PER)`, `Location (LOC)`, `Organisation (ORG)`, `Event (EVT)` and `Time (TIME)`. It also happens that the model identifies entities where the entity type cannot be determined and thus these will have an unkown entity attached.

Here's a sample request to the API (note: installation of http-test library can be done on any linux computer by `apt-get install httpie`):

```bash
http POST http://127.0.0.1:8081/named-entity-recognition/predict text="Obama bor i vitahuset, han kommer flytta därifrån om tre dagar"
```

The response you'll get looks something like this:

```js
{
    "tokens": [
        { "word": "Obama", "start": 0, "end": 4, "entity": "PER", "score": 0.9987 },
        { "word": "vitahuset", "entity": "LOC", ...},
        {"word": "tre", "entity": "TIME", ...},
        {"word": "dagar", "entity": "TIME", ...}
    ]
}
```

## Installation

Install the dependencies:

```sh
pipenv install --dev
```

## Test the setup

Start the HTTP server:

```sh
bin/start_server
```

Send a test request:

```sh
bin/test_request
```

## Run helm dockerfile

To be able to run application in docker

```sh
./bin/build_and_tag
./bin/start_docker_server
```

## Run helm kubernetes
To run in kubernetes first follow instructions at: [](https://confluence.intern.bolagsverket.se/display/VERKTYG/Installera+Helm)
Then build the docker image and install the helm chart in this repo:

```sh
./bin/build_and_tag
helm install bms helm -n bert-models
```
