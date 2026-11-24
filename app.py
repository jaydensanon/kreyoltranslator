"""Web front end for the Kreyòl <-> English translator.

Run:  python app.py   then open http://127.0.0.1:5000
"""
from flask import Flask, redirect, render_template, request, url_for

from translator import CORE, KREYOL_CORE, Translator, base

app = Flask(__name__)
translator = Translator()          # loading the dictionary is slow: do it once

LANGUAGES = {"english": "English", "kreyol": "Kreyòl"}

# English sentences that show a word in use, by word class. Each is translated with the
# sentence translator; the first one whose Kreyòl output contains the word is used.
EXAMPLES = {
    "n": ["I see the {}.", "I like the {}.", "The {} is here."],
    "v": ["We want to {}.", "I {} every day.", "They {} now."],
    "adj": ["I am {}.", "She is very {}.", "The house is {}."],
    "adv": ["We eat {}.", "I work {}."],
}


def is_single_word(text):
    return len(text.split()) == 1 and text[-1] not in "?!."


def english_tag(word):
    """Most likely word class of an English word."""
    if word in CORE:
        return next(iter(CORE[word]))
    tags = translator.eng_tags.get(word) or {base(t) for _, t, *_ in translator.eng_to_kreyol.get(word, [])}
    for tag in ("n", "v", "adj", "adv"):
        if tag in tags:
            return tag
    return next(iter(tags), None)


def english_lemma(word):
    """Dictionary form of an English word ('dogs' -> 'dog', 'ate' -> 'eat')."""
    if translator.knows_english(word):
        return word
    for lemma in (translator.lemma_verb(word), translator.lemma_noun(word), translator.lemma_adj(word)):
        if lemma and translator.knows_english(lemma[0]):
            return lemma[0]
    return word


def example_sentence(english_word, kreyol_word, tag):
    """(Kreyòl sentence, English sentence) using the word, or None."""
    for template in EXAMPLES.get(tag, []):
        english = template.format(english_word)
        kreyol, _ = translator.translate_sentence(english, "english")
        if kreyol_word.casefold() in kreyol.casefold():
            return kreyol, english
    return None


def translate_word(word, source=None):
    w = word.casefold()
    source = source or translator.detect_language(w)
    if source == "kreyol":
        senses = translator.to_english(w)
        known = senses or w in KREYOL_CORE
        best = translator.english_for(w) if known else None
        return {
            "source": "kreyol",
            "target": "english",
            "translation": best,
            "others": [e for e in dict.fromkeys(senses) if e != best],
            "example": None,
        }

    lemma = english_lemma(w)
    tag = english_tag(lemma)
    best = translator.kreyol_for(lemma, tag) if translator.knows_english(lemma) else None
    # English dictionary only: lookup() would prefer the Kreyòl reading of a shared spelling
    others = translator.to_kreyol(w) or translator.to_kreyol(lemma)
    if not best and others:
        best = others[0]
    example = example_sentence(lemma, best, tag) if best else None
    return {
        "source": "english",
        "target": "kreyol",
        "translation": best,
        "others": [k for k in dict.fromkeys(others) if k != best],
        "example": example,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/translate")
def translate():
    text = request.args.get("text", "").strip()
    chosen = request.args.get("from")
    chosen = chosen if chosen in LANGUAGES else None      # None = detect automatically
    if not text:
        return redirect(url_for("index"))

    single = is_single_word(text)
    if single:
        result = translate_word(text, chosen)
    else:
        translation, source = translator.translate_sentence(text, chosen)
        result = {
            "source": source,
            "target": "english" if source == "kreyol" else "kreyol",
            "translation": translation,
            "others": [],
            "example": None,
        }
    # A word spelled the same in both languages: offer the other reading
    w = text.casefold()
    other = result["target"]
    in_both = single and w in translator.kreyol_to_eng and translator.knows_english(english_lemma(w))
    switch_url = url_for("translate", text=text, **{"from": other}) if in_both else None
    return render_template(
        "result.html",
        text=text,
        single=single,
        switch_url=switch_url,
        switch_name=LANGUAGES[other],
        source_name=LANGUAGES[result["source"]],
        target_name=LANGUAGES[result["target"]],
        **result,
    )


if __name__ == "__main__":
    app.run(debug=True)
