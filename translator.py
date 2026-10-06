"""Haitian Kreyòl <-> English translator.

Single words are looked up in the dictionary (tagged with word classes by tag_wordlist).
Whole sentences are parsed and rebuilt with the grammar rules in sentence_structure.
"""
import re
from pathlib import Path

import tag_wordlist as tw
from sentence_structure import SentenceRules

HERE = Path(__file__).resolve().parent
GLOSS_TAG = re.compile(r"^(.*?)\s*\(([a-z.]+)(\?)?\)$")


def base(tag):
    return tag.split(".")[0] if tag else tag


# ---- core vocabulary ----------------------------------------------------------
# Preferred translations for common words, checked before the dictionary.
# CORE[english][tag] = kreyol          KREYOL_CORE[kreyol][tag] = english

CORE, KREYOL_CORE = {}, {}


def _core(tag, pairs):
    for pair in pairs.split(","):
        eng, kreyol = (p.strip() for p in pair.split("="))
        CORE.setdefault(eng, {}).setdefault(tag, kreyol)
        KREYOL_CORE.setdefault(kreyol, {}).setdefault(tag, eng)


_core("v", """eat=manje, go=ale, come=vini, see=wè, want=vle, know=konnen, love=renmen,
    like=renmen, have=gen, need=bezwen, speak=pale, talk=pale, say=di, tell=di, give=bay,
    do=fè, make=fè, buy=achte, sleep=dòmi, drink=bwè, read=li, write=ekri, sit=chita,
    understand=konprann, walk=mache, call=rele, hear=tande, run=kouri, work=travay, play=jwe,
    learn=aprann, help=ede, cook=kwit, wait=tann, leave=pati, arrive=rive, open=louvri,
    close=fèmen, sing=chante, dance=danse, think=panse, sell=vann, take=pran, put=mete,
    find=jwenn, look=gade, watch=gade, wash=lave, teach=anseye, cry=kriye, laugh=ri, live=viv,
    stay=rete, become=vin, bring=pote, carry=pote, send=voye, pay=peye, ask=mande,
    answer=reponn, finish=fini, start=kòmanse, begin=kòmanse, believe=kwè, forget=bliye,
    remember=sonje, hate=rayi, lose=pèdi, die=mouri, kill=touye, swim=naje, travel=vwayaje,
    visit=vizite, clean=netwaye, enter=antre, return=retounen, stand=kanpe, show=montre,
    try=eseye, use=sèvi, cost=koute, listen=koute, seem=sanble, meet=rankontre, pray=priye,
    happen=rive, steal=vòlè, can=kapab""")
_core("n", """man=nonm, woman=fanm, child=timoun, kid=timoun, son=pitit gason,
    daughter=pitit fi, boy=ti gason, girl=tifi, friend=zanmi, house=kay, home=lakay, car=machin,
    dog=chen, cat=chat, water=dlo, money=lajan, book=liv, school=lekòl, family=fanmi,
    mother=manman, mom=manman, father=papa, dad=papa, brother=frè, sister=sè, day=jou,
    night=lannwit, week=semèn, year=ane, month=mwa, rice=diri, bread=pen, coffee=kafe,
    food=manje, meat=vyann, fish=pwason, chicken=poul, bean=pwa, fruit=fwi, country=peyi,
    city=vil, town=vil, church=legliz, teacher=pwofesè, doctor=doktè, student=elèv, job=travay,
    work=travay, table=tab, chair=chèz, door=pòt, name=non, time=tan, people=moun, person=moun,
    thing=bagay, market=mache, sea=lanmè, sun=solèy, rain=lapli, hand=men, head=tèt, eye=je,
    heart=kè, road=wout, street=lari, tree=pyebwa, life=lavi, god=Bondye, language=lang,
    creole=kreyòl, kreyol=kreyòl, english=angle, french=franse, haiti=Ayiti, morning=maten,
    evening=aswè, soccer=foutbòl, music=mizik, song=chante, phone=telefòn, love=lanmou,
    problem=pwoblèm, question=kesyon, word=mo, sentence=fraz, baby=tibebe, wife=madanm,
    husband=mari, store=magazen, meal=manje, bed=kabann, room=chanm, love=lanmou""")
_core("adj", """big=gwo, large=gwo, small=piti, little=ti, beautiful=bèl, pretty=bèl,
    nice=bèl, good=bon, bad=move, old=vye, new=nouvo, young=jenn, tall=wo, short=kout,
    red=wouj, white=blan, black=nwa, blue=ble, green=vèt, yellow=jòn, happy=kontan, sad=tris,
    tired=fatige, hungry=grangou, thirsty=swaf, sick=malad, hot=cho, cold=frèt, sweet=dous,
    rich=rich, poor=pòv, strong=fò, ugly=lèd, easy=fasil, difficult=difisil, hard=difisil,
    clean=pwòp, dirty=sal, full=plen, empty=vid, far=lwen, ready=pare, true=vre,
    important=enpòtan, first=premye, last=dènye, fine=byen""")
_core("adv", """today=jodi a, tomorrow=demen, yesterday=yè, now=kounye a, here=isit, there=la,
    home=lakay, well=byen, also=tou, too=tou, again=ankò, always=toujou, still=toujou,
    together=ansanm, soon=talè, later=pita, a_lot=anpil, much=anpil, slowly=dousman,
    quickly=vit, fast=vit, please=tanpri, early=bonè, tonight=aswè a, really=vrèman,
    maybe=petèt, only=sèlman, outside=deyò, inside=anndan, everywhere=toupatou, very=anpil""")
_core("intj", """hello=bonjou, hi=alo, yes=wi, no=non, thanks=mèsi, thank_you=mèsi,
    goodbye=orevwa, bye=babay, good_morning=bonjou, good_evening=bonswa, okay=dakò, ok=dakò""")

# Whole sentences that do not translate word by word
IDIOMS = {
    "how are you": "Kouman ou ye?",
    "what is your name": "Kijan ou rele?",
    "thank you": "Mèsi.",
    "thank you very much": "Mèsi anpil.",
    "good morning": "Bonjou.",
    "good evening": "Bonswa.",
    "see you later": "N a wè pita.",
    "i am fine": "Mwen byen.",
}
KREYOL_IDIOMS = {
    "kijan ou rele": "What is your name?",
    "kouman ou rele": "What is your name?",
    "mèsi anpil": "Thank you very much.",
    "n a wè pita": "See you later.",
    "sak pase": "What's up?",
    "n ap boule": "We're doing fine.",
    "mwen byen": "I am fine.",
}

# ---- English morphology -------------------------------------------------------

IRREGULAR = """be was been, have had had, do did done, go went gone, come came come,
    see saw seen, eat ate eaten, drink drank drunk, give gave given, take took taken,
    make made made, know knew known, say said said, tell told told, get got gotten,
    buy bought bought, bring brought brought, think thought thought, find found found,
    sit sat sat, sleep slept slept, leave left left, feel felt felt, keep kept kept,
    run ran run, write wrote written, read read read, speak spoke spoken, hear heard heard,
    meet met met, pay paid paid, put put put, sell sold sold, teach taught taught,
    understand understood understood, stand stood stood, lose lost lost, win won won,
    begin began begun, sing sang sung, swim swam swum, fall fell fallen,
    forget forgot forgotten, become became become, break broke broken, choose chose chosen,
    drive drove driven, fly flew flown, grow grew grown, hold held held, hurt hurt hurt,
    lead led led, let let let, mean meant meant, ride rode ridden, ring rang rung,
    rise rose risen, send sent sent, shake shook shaken, shoot shot shot, shut shut shut,
    spend spent spent, steal stole stolen, throw threw thrown, wake woke woken,
    wear wore worn, cut cut cut, hit hit hit, cost cost cost, bite bit bitten,
    build built built, catch caught caught, draw drew drawn, feed fed fed, fight fought fought,
    hang hung hung, hide hid hidden, lend lent lent, seek sought sought, sweep swept swept,
    weep wept wept, bleed bled bled, blow blew blown, dig dug dug, forgive forgave forgiven,
    freeze froze frozen, sink sank sunk, light lit lit, quit quit quit"""
IRR_FORMS, IRR_PAST, IRR_PP = {}, {}, {}
for _entry in IRREGULAR.split(","):
    _base, _past, _pp = _entry.split()
    IRR_FORMS[_base] = (_past, _pp)
    IRR_PAST.setdefault(_past, _base)
    IRR_PP.setdefault(_pp, _base)
IRR_PAST["were"] = "be"
SAME_FORM = {b for b, (p, _) in IRR_FORMS.items() if b == p}      # read, put, cut ...

IRR_PLURAL = {"children": "child", "men": "man", "women": "woman", "people": "person",
              "feet": "foot", "teeth": "tooth", "mice": "mouse", "geese": "goose"}
PLURAL_OF = {v: k for k, v in IRR_PLURAL.items()}
PLURAL_OF["person"] = "people"
IRR_ADJ = {"better": "good", "best": "good", "worse": "bad", "worst": "bad"}
VOWELS_EN = "aeiou"


def _cvc(w):
    """Short consonant-vowel-consonant word whose last letter doubles (stop -> stopped)."""
    groups = re.findall(r"[aeiou]+", w)
    return (len(w) >= 3 and len(groups) == 1 and w[-1] not in VOWELS_EN + "wxy"
            and w[-2] in VOWELS_EN and w[-3] not in VOWELS_EN)


def ing(w):
    if w.endswith("ie"):
        return w[:-2] + "ying"
    if w.endswith("e") and not w.endswith(("ee", "ye", "oe")) and w != "be":
        return w[:-1] + "ing"
    return w + w[-1] + "ing" if _cvc(w) else w + "ing"


def past(w):
    if w in IRR_FORMS:
        return IRR_FORMS[w][0]
    if w.endswith("e"):
        return w + "d"
    if w.endswith("y") and w[-2:-1] not in VOWELS_EN:
        return w[:-1] + "ied"
    return w + w[-1] + "ed" if _cvc(w) else w + "ed"


def past_participle(w):
    return IRR_FORMS[w][1] if w in IRR_FORMS else past(w)


def third(w):
    special = {"have": "has", "be": "is", "do": "does", "go": "goes"}
    if w in special:
        return special[w]
    if w.endswith(("s", "x", "z", "ch", "sh", "o")):
        return w + "es"
    if w.endswith("y") and w[-2:-1] not in VOWELS_EN:
        return w[:-1] + "ies"
    return w + "s"


def plural(noun):
    words = noun.split()
    last = words[-1]
    if last in PLURAL_OF:
        last = PLURAL_OF[last]
    elif last.endswith(("s", "x", "z", "ch", "sh")):
        last += "es"
    elif last.endswith("y") and last[-2:-1] not in VOWELS_EN:
        last = last[:-1] + "ies"
    else:
        last += "s"
    return " ".join(words[:-1] + [last])


def with_article(phrase):
    return ("an " if phrase[:1].lower() in VOWELS_EN else "a ") + phrase


def be_form(agr, tense):
    if tense == "past":
        return "were" if agr == "pl" else "was"
    return {"1s": "am", "3s": "is"}.get(agr, "are")


def do_form(agr, tense):
    if tense == "past":
        return "did"
    return "does" if agr == "3s" else "do"


def inflect_first(lemma, fn):
    first, _, rest = lemma.partition(" ")
    return " ".join([fn(first)] + ([rest] if rest else []))


def english_vp(lemma, agr, tense="present", modal=None, prog=False, going=False,
               used=False, adv=None, neg=False, never=False, question=False):
    """Build an English verb phrase. Returns (words, has_aux); when has_aux is true,
    words[0] is the auxiliary that moves in front of the subject in a question."""
    nots = (["not"] if neg else []) + (["never"] if never else [])
    advs = [adv] if adv else []
    if used:
        if neg or question:
            return ["did"] + nots + ["use", "to", lemma], True
        return ["used", "to", lemma], False
    if going:
        return [be_form(agr, tense)] + nots + ["going", "to", lemma], True
    if modal:
        main = ["be", inflect_first(lemma, ing)] if prog else [lemma]
        return [modal] + nots + advs + main, True
    if prog:
        return [be_form(agr, tense)] + nots + advs + [inflect_first(lemma, ing)], True
    if lemma == "be":
        return [be_form(agr, tense)] + nots + advs, True
    if neg or question:
        return [do_form(agr, tense)] + nots + advs + [lemma], True
    if tense == "past":
        main = inflect_first(lemma, past)
    else:
        main = inflect_first(lemma, third) if agr == "3s" else lemma
    return (["never"] if never else []) + advs + [main], False


# ---- English grammar words --------------------------------------------------------

EN_SUBJ = {"i": "i", "you": "you", "he": "he", "she": "she", "it": "it", "we": "we", "they": "they"}
EN_OBJ = {"me": "i", "you": "you", "him": "he", "her": "she", "it": "it", "us": "we", "them": "they"}
EN_POSS = {"my": "i", "your": "you", "his": "he", "her": "she", "its": "it", "our": "we", "their": "they"}
EN_POSS_PRON = {"mine": "i", "yours": "you", "hers": "she", "ours": "we", "theirs": "they"}
EN_REFLEXIVE = {"myself": "i", "yourself": "you", "himself": "he", "herself": "she", "itself": "it",
                "ourselves": "we", "yourselves": "you_pl", "themselves": "they"}
EN_DET = {"the": "the", "a": "a", "an": "a", "this": "this", "that": "this", "these": "these",
          "those": "these"}
EN_QUANT = {"each": "each", "every": "every", "all": "all", "some": "some", "several": "several",
            "many": "many", "a_lot_of": "many", "much": "many", "other": "other",
            "enough": "enough", "same": "same"}
EN_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
          "eight": 8, "nine": 9, "ten": 10}
EN_STANDALONE = {"everyone": "tout moun", "everybody": "tout moun", "someone": "yon moun",
                 "somebody": "yon moun", "something": "yon bagay", "everything": "tout bagay",
                 "this": "sa", "that": "sa", "these": "sa yo", "those": "sa yo"}
EN_NEG_WORDS = {"nothing": "nothing", "anything": "nothing", "nobody": "nobody",
                "anybody": "nobody", "anyone": "nobody", "anymore": "anymore",
                "no_longer": "anymore", "at_all": "not_at_all", "yet": "not_yet"}
BE = {"am": "present", "is": "present", "are": "present", "was": "past", "were": "past",
      "be": "base", "been": "pp", "being": "ing"}
DO = {"do": "present", "does": "present", "did": "past"}
HAVE = {"have": "present", "has": "present", "had": "past"}
MODAL_TENSE = {"will": "future", "shall": "future", "would": "conditional", "should": "should",
               "must": "must", "can": "can", "could": "could", "may": "can", "might": "conditional"}
AUX = set(BE) | set(DO) | set(HAVE) | set(MODAL_TENSE)
EN_Q = {"what": "what", "who": "who", "whom": "who", "where": "where", "when": "when",
        "how": "how", "why": "why", "which": "which", "how_much": "how_much", "how_many": "how_many"}
EN_CONNECT = {"and": "and_then", "but": "but", "or": "or", "because": "because", "so": "so",
              "if": "if", "when": "when", "while": "while", "since": "since", "then": "and_then",
              "even_if": "even_if", "so_that": "so_that"}
SUBORDINATE = {"if", "when", "while", "since", "even_if"}   # connect() puts these first
EN_PREP = {"in": "in", "into": "in", "at": "at", "to": "to", "on": "on", "about": "about",
           "under": "under", "above": "above", "over": "above", "in_front_of": "in_front_of",
           "behind": "behind", "beside": "beside", "next_to": "beside", "with": "with",
           "for": "for", "from": "from", "inside": "inside", "outside": "outside",
           "between": "between", "before": "before", "after": "after", "without": "without",
           "until": "until", "against": "against", "near": "toupre", "during": "pandan",
           "because_of": "akoz", "of": "de", "by": "pa"}
MOTION = {"go", "come", "arrive", "return", "travel", "walk", "run", "leave", "drive", "fly",
          "move", "get", "send", "bring", "carry"}
HABIT = {"usually", "always", "often", "sometimes"}
LOCATION_WORDS = {"here", "there", "home", "outside", "inside", "upstairs", "downstairs"}

EN_CONTRACTIONS = [
    (r"\bcan't\b", "can not"), (r"\bcannot\b", "can not"), (r"\bwon't\b", "will not"),
    (r"\bshan't\b", "shall not"), (r"n't\b", " not"), (r"'m\b", " am"), (r"'re\b", " are"),
    (r"'ve\b", " have"), (r"'ll\b", " will"), (r"'d\b", " would"), (r"\blet's\b", "let us"),
    (r"\b(he|she|it|that|what|where|who|there|here|how)'s\b", r"\1 is"), (r"'s\b", " 's"),
]
EN_PHRASES = [
    ("in front of", "in_front_of"), ("next to", "next_to"), ("a lot of", "a_lot_of"),
    ("a lot", "a_lot"), ("how much", "how_much"), ("how many", "how_many"), ("at all", "at_all"),
    ("any more", "anymore"), ("no longer", "no_longer"), ("no one", "nobody"),
    ("thank you", "thank_you"), ("good morning", "good_morning"),
    ("good evening", "good_evening"), ("even if", "even_if"), ("even though", "even_if"),
    ("so that", "so_that"), ("have to", "have_to"), ("has to", "has_to"), ("had to", "had_to"),
    ("because of", "because_of"),
]

# ---- Kreyòl grammar words ----------------------------------------------------------

KR_PRONOUN = {"mwen": "i", "m": "i", "ou": "you", "w": "you", "li": "he", "l": "he",
              "nou": "we", "n": "we", "yo": "they", "y": "they"}
EN_SUBJ_FORM = {"i": "I", "you": "you", "he": "he/she", "we": "we", "they": "they"}
EN_OBJ_FORM = {"i": "me", "you": "you", "he": "him/her", "we": "us", "they": "them"}
EN_POSS_FORM = {"i": "my", "you": "your", "he": "his/her", "we": "our", "they": "their"}
EN_POSS_PRON_FORM = {"i": "mine", "you": "yours", "he": "his/hers", "we": "ours", "they": "theirs"}
AGREEMENT = {"i": "1s", "he": "3s"}

KR_NORMAL = {"t": "te", "p": "pa", "k": "ki", "ape": "ap", "pe": "ap", "ava": "va",
             "prale": "pral", "pra": "pral", "pwal": "pral", "fenk": "fèk", "sòt": "sot",
             "kab": "ka", "kon": "konn", "on": "yon", "lan": "nan"}
KR_PHRASES = {
    ("kounye", "a"): "@now", ("konnya",): "@now", ("kounya",): "@now", ("jodi", "a"): "@today",
    ("ki", "moun"): "?who", ("kiyès",): "?who", ("ki", "kote"): "?where", ("kote",): "?where",
    ("ki", "lè"): "?when", ("kilè",): "?when", ("ki", "jan"): "?how", ("kijan",): "?how",
    ("kouman",): "?how", ("kòman",): "?how", ("poukisa",): "?why", ("pouki",): "?why",
    ("kisa",): "?what", ("ki", "sa"): "?what", ("konbyen",): "?how much",
    ("sa", "a"): "#this", ("sa", "yo"): "#these", ("sa",): "#that", ("pa", "vre"): "#tag", ("bò", "kote"): "bò kote",
}
KR_DET = {"la": "the", "a": "the", "an": "the", "nan": "the", "yo": "pl", "#this": "this",
          "#these": "these"}
KR_QUANT = {"chak": "each", "tout": "all", "kèk": "some", "plizyè": "several", "anpil": "many",
            "okenn": "no", "lòt": "other", "menm": "same", "ase": "enough"}
KR_NUM = {"de": 2, "twa": 3, "kat": 4, "senk": 5, "sis": 6, "sèt": 7, "uit": 8, "nèf": 9, "dis": 10}
EN_NUM_WORD = {v: k for k, v in EN_NUM.items()}
KR_PREP = {"nan": "in", "sou": "on", "anba": "under", "anwo": "above", "devan": "in front of",
           "dèyè": "behind", "bò kote": "beside", "akote": "beside", "ak": "with",
           "avèk": "with", "avè": "with", "pou": "for", "soti": "from", "sot": "from",
           "kot": "at", "anndan": "inside", "deyò": "outside", "ant": "between",
           "anvan": "before", "apre": "after", "san": "without", "jis": "until",
           "kont": "against", "toupre": "near", "pre": "near", "lakay": "at home"}
KR_CONNECT = {"epi": "and", "e": "and", "men": "but", "oswa": "or", "paske": "because",
              "donk": "so", "kidonk": "so", "si": "if", "lè": "when", "pandan": "while",
              "kòm": "since", "menmsi": "even if"}
KR_END_NEG = {"anyen": ("anything", "nothing"), "pèsonn": ("anybody", "nobody"),
              "ankò": ("anymore", "again"), "ditou": ("at all", "at all")}
KR_MARKERS = {"pa", "poko", "janm", "te", "ap", "va", "pral", "ta", "fèk", "sot", "fin",
              "konn", "dwe", "ka", "kapab", "vin"}
KR_LOCATION = {"la": "there", "isit": "here", "lakay": "at home", "deyò": "outside",
               "anndan": "inside"}
Q_ENGLISH = {"who": "who", "what": "what", "where": "where", "when": "when", "how": "how",
             "why": "why", "how much": "how much", "which": "which"}

KREYOL_FUNCTION = {"mwen", "ou", "li", "nou", "yo", "pa", "ap", "te", "se", "la", "nan", "sa",
                   "ki", "yon", "gen", "èske", "kisa", "kote", "pou", "ak", "m", "w", "l", "n",
                   "y", "t", "pral", "poko", "kounye", "konn", "vle", "kijan", "kouman"}
ENGLISH_FUNCTION = {"the", "is", "are", "am", "was", "were", "i", "you", "he", "she", "it", "we",
                    "they", "do", "does", "did", "not", "to", "of", "and", "will", "have", "has",
                    "my", "your", "this", "that", "what", "where", "who", "how", "why", "in",
                    "on", "with", "for", "be", "can", "me", "him", "her", "us", "them", "don't"}


class Translator:
    def __init__(self, path=None):
        self.rules = SentenceRules()
        self.kreyol_to_eng = {}     # kreyol -> [(english, tag, confident)]
        self.eng_to_kreyol = {}     # english -> [(kreyol, tag, confident, position, n_glosses)]
        self.eng_tags = {}          # english -> {confident base tags}
        tagged = HERE / "wordlist_tagged.csv"
        path = Path(path) if path else (tagged if tagged.exists() else HERE / "wordlist.csv")
        self._load(path)
        self.en_to_kr = EnglishToKreyol(self)
        self.kr_to_en = KreyolToEnglish(self)

    def _load(self, path):
        with open(path, encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]
        if not any(GLOSS_TAG.match(g.strip()) for line in lines[:50] if " -> " in line
                   for g in line.split(" -> ")[1].split(",")):
            lines = tw.tag_lines(lines)[0]          # untagged dictionary: tag it in memory
        for line in lines:
            parts = line.split(" -> ")
            if len(parts) != 2:
                continue
            kreyol = parts[0].strip().casefold()
            glosses = [g.strip() for g in parts[1].split(",") if g.strip()]
            for pos, gloss in enumerate(glosses):
                m = GLOSS_TAG.match(gloss)
                eng, tag, unsure = (m.group(1), m.group(2), m.group(3)) if m else (gloss, "n", "?")
                eng = eng.strip().casefold()
                if not eng:
                    continue
                self.kreyol_to_eng.setdefault(kreyol, []).append((eng, tag, not unsure))
                self.eng_to_kreyol.setdefault(eng, []).append(
                    (kreyol, tag, not unsure, pos, len(glosses)))
                if not unsure:
                    self.eng_tags.setdefault(eng, set()).add(base(tag))

    # ---- word lookups -----------------------------------------------------------

    def to_english(self, word):
        return [e for e, _, _ in self.kreyol_to_eng.get(word.strip().casefold(), [])]

    def to_kreyol(self, word):
        return [k for k, *_ in self.eng_to_kreyol.get(word.strip().casefold(), [])]

    def translate(self, word):
        """Look up one word in either direction (falls back to its dictionary form)."""
        result = self.to_english(word) or self.to_kreyol(word)
        if not result:
            w = word.strip().casefold()
            for lemma in (self.lemma_verb(w), self.lemma_noun(w), self.lemma_adj(w)):
                if lemma and lemma[0] != w:
                    result = self.to_kreyol(lemma[0])
                    if result:
                        break
        return result

    def lookup(self, word):
        """Like translate(), but each result carries its word class: [(word, tag)]."""
        w = word.strip().casefold()
        if w in self.kreyol_to_eng:
            return [(e, t) for e, t, _ in self.kreyol_to_eng[w]]
        if w in self.eng_to_kreyol:
            return [(k, t) for k, t, *_ in self.eng_to_kreyol[w]]
        return [(k, "") for k in self.translate(w)]

    def kreyol_for(self, eng, tag=None):
        """Best Kreyòl word for an English word, preferring the wanted word class."""
        eng = eng.casefold()
        if eng in CORE:
            if tag in CORE[eng]:
                return CORE[eng][tag]
            if tag is None or not any(base(t) == tag for _, t, *_ in self.eng_to_kreyol.get(eng, [])):
                return next(iter(CORE[eng].values()))
        candidates = self.eng_to_kreyol.get(eng)
        if not candidates:
            return eng
        kreyol_words = self.kreyol_to_eng

        def score(c):
            kreyol, t, confident, pos, count = c
            s = (4 if tag and base(t) == tag else 0) + (1 if confident else 0) - 0.7 * pos - 0.05 * count
            if kreyol.startswith("la") and kreyol[2:] in kreyol_words:
                s -= 2                      # agglutinated article (labatwa), we add our own
            if re.search(r"r[oò]", kreyol):
                s -= 1                      # older spelling (rouj, gro) instead of wouj, gwo
            return s
        return max(candidates, key=score)[0]

    def english_for(self, kreyol, tag=None):
        """Best English word for a Kreyòl word, preferring the wanted word class."""
        k = kreyol.casefold()
        if k in KREYOL_CORE:
            if tag in KREYOL_CORE[k]:
                return KREYOL_CORE[k][tag]
            if tag is None:
                return next(iter(KREYOL_CORE[k].values()))
        glosses = self.kreyol_to_eng.get(k)
        if not glosses:
            return KREYOL_CORE[k][next(iter(KREYOL_CORE[k]))] if k in KREYOL_CORE else kreyol
        for want_confident in (True, False):
            for eng, t, confident in glosses:
                if (tag is None or base(t) == tag) and (confident or not want_confident):
                    return re.sub(r"^be ", "", eng) if tag in ("adj", "n") else eng
        return glosses[0][0]

    def kreyol_has(self, kreyol, tag):
        k = kreyol.casefold()
        if k in KREYOL_CORE:
            return tag in KREYOL_CORE[k]
        return any(base(t) == tag for _, t, _ in self.kreyol_to_eng.get(k, []))

    # ---- English word classes and dictionary forms --------------------------------

    def is_verb(self, lemma):
        return (lemma in tw.VERBS or lemma in tw.STATIVE_VERBS or "v" in CORE.get(lemma, {})
                or "v" in self.eng_tags.get(lemma, ()))

    def is_noun(self, lemma):
        return "n" in CORE.get(lemma, {}) or "n" in self.eng_tags.get(lemma, ())

    def is_adj(self, word):
        lemma = self.lemma_adj(word)[0]
        return (lemma in tw.ADJECTIVES or "adj" in CORE.get(lemma, {})
                or "adj" in self.eng_tags.get(lemma, ()))

    def knows_english(self, word):
        return word in self.eng_to_kreyol or word in CORE

    def lemma_verb(self, w):
        """'ate' -> ('eat', 'past'). Form is base, s, past, pp or ing. None if not a verb."""
        if not w or not w.isalpha():
            return None
        if w in IRR_PAST and w not in SAME_FORM:
            return IRR_PAST[w], "past"
        if w in IRR_PP and w not in SAME_FORM and not self.is_verb(w):
            return IRR_PP[w], "pp"
        if self.is_verb(w):
            return w, "base"
        candidates = []
        if w.endswith("ing") and len(w) > 4:
            stem = w[:-3]
            candidates = [(stem, "ing"), (stem + "e", "ing"), (stem[:-1], "ing")]
            if stem.endswith("y"):
                candidates.append((stem[:-1] + "ie", "ing"))
        elif w.endswith("ied"):
            candidates = [(w[:-3] + "y", "past")]
        elif w.endswith("ed"):
            candidates = [(w[:-2], "past"), (w[:-1], "past"), (w[:-3], "past")]
        elif w.endswith("ies"):
            candidates = [(w[:-3] + "y", "s")]
        elif w.endswith("es"):
            candidates = [(w[:-2], "s"), (w[:-1], "s")]
        elif w.endswith("s") and not w.endswith("ss"):
            candidates = [(w[:-1], "s")]
        for lemma, form in candidates:
            if self.is_verb(lemma):
                return lemma, form
        return None

    def lemma_noun(self, w):
        """'books' -> ('book', True). Returns (lemma, plural)."""
        if w in IRR_PLURAL:
            return IRR_PLURAL[w], True
        if self.is_noun(w) or w in CORE or not w.endswith("s") or w.endswith(("ss", "us", "is")):
            return w, False
        candidates = [w[:-1]]
        if w.endswith("ies"):
            candidates.insert(0, w[:-3] + "y")
        if w.endswith("ves"):
            candidates += [w[:-3] + "f", w[:-3] + "fe"]
        if w.endswith("es"):
            candidates.insert(0, w[:-2])
        for c in candidates:
            if self.is_noun(c) or c in CORE or c in self.eng_to_kreyol:
                return c, True
        return w[:-1], True

    def lemma_adj(self, w):
        """'bigger' -> ('big', 'comp'), 'best' -> ('good', 'sup'), 'red' -> ('red', None)."""
        if w in IRR_ADJ:
            return IRR_ADJ[w], "sup" if w.endswith("st") else "comp"
        for suffix, kind in (("est", "sup"), ("er", "comp")):
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                stem = w[:-len(suffix)]
                for c in (stem, stem + "e", stem[:-1], stem[:-1] + "y" if stem.endswith("i") else None):
                    if c and (c in tw.ADJECTIVES or "adj" in CORE.get(c, {})
                              or "adj" in self.eng_tags.get(c, ())):
                        return c, kind
        return w, None

    # ---- sentences ----------------------------------------------------------------

    def detect_language(self, text):
        words = re.findall(r"[^\W\d_]+", text.casefold().replace("'", " "))
        kreyol = sum(w in KREYOL_FUNCTION or (w in self.kreyol_to_eng and w not in self.eng_to_kreyol)
                     for w in words)
        english = sum(w in ENGLISH_FUNCTION or (w in self.eng_to_kreyol and w not in self.kreyol_to_eng)
                      for w in words)
        return "kreyol" if kreyol > english else "english"

    def translate_sentence(self, text, source=None):
        """Translate a whole sentence. Returns (translation, source language)."""
        self.rules.explain(clear=True)
        source = source or self.detect_language(text)
        converter = self.kr_to_en if source == "kreyol" else self.en_to_kr
        sentences = re.findall(r"[^.!?]+[.!?]*", text) or [text]
        return " ".join(converter.translate(s) for s in sentences if s.strip()), source

    def explain(self):
        """Grammar rules (id, text) used by the last English -> Kreyòl translation."""
        return self.rules.explain(clear=False)


class EnglishToKreyol:
    """Parse an English sentence and rebuild it with SentenceRules."""

    def __init__(self, translator):
        self.tr = translator
        self.rules = translator.rules

    def translate(self, text):
        text = text.strip()
        mark = text[-1] if text[-1:] in "?!." else "."
        key = re.sub(r"[^\w\s']", "", text.casefold()).strip()
        if key in IDIOMS:
            return IDIOMS[key]
        tokens = self.tokenize(text)
        if not tokens:
            return text
        segments = self.split_clauses(tokens, mark == "?")
        pieces = [(conn, self.clause(seg, mark)) for conn, seg in segments if seg]
        if not pieces:
            return text
        R = self.rules
        if pieces[0][0] in SUBORDINATE and len(pieces) > 1:
            result = R.connect(pieces[0][1], pieces[1][1], EN_CONNECT[pieces[0][0]])
            rest = pieces[2:]
        else:
            result, rest = pieces[0][1], pieces[1:]
        for conn, clause in rest:
            kind = EN_CONNECT.get(conn, "and_then")
            result = R.connect(clause, result, kind) if conn in SUBORDINATE else R.connect(result, clause, kind)
        return R.finish(result, mark)

    def tokenize(self, text):
        t = text.replace("’", "'").replace("‘", "'")
        for pattern, replacement in EN_CONTRACTIONS:
            t = re.sub(pattern, replacement, t, flags=re.I)
        for phrase, token in EN_PHRASES:
            t = re.sub(r"\b" + phrase + r"\b", token, t, flags=re.I)
        return [(w.casefold(), w) for w in re.findall(r"'s|[^\W\d]+|\d+|,", t)]

    # ---- clause splitting ----------------------------------------------------------

    def split_clauses(self, toks, question):
        segments = [[None, []]]
        for i, (t, _) in enumerate(toks):
            current = segments[-1]
            if t in EN_CONNECT and not (i == 0 and question and t in EN_Q):
                if not current[1] and current[0] is None:
                    current[0] = t                       # sentence starts with "If ..."
                    continue
                has_verb = any(x in AUX or self.verb_form(x) for x, _ in current[1])
                if self.starts_clause(toks, i + 1) and (has_verb or t not in ("and", "or")):
                    segments.append([t, []])
                    continue
            if t == ",":
                if current[0] in SUBORDINATE and self.starts_clause(toks, i + 1):
                    segments.append([None, []])
                continue
            current[1].append(toks[i])
        return [(c, s) for c, s in segments]

    def starts_clause(self, toks, j):
        if j >= len(toks):
            return False
        if toks[j][0] in EN_SUBJ or toks[j][0] == "there":
            return True
        np, k = self.parse_np(toks, j)
        return bool(np) and k < len(toks) and (toks[k][0] in AUX or self.verb_form(toks[k][0]) is not None)

    # ---- word helpers ----------------------------------------------------------------

    def verb_form(self, w):
        if not w or w in EN_DET or w in EN_SUBJ or w in EN_OBJ or w in EN_POSS or w in AUX:
            return None
        return self.tr.lemma_verb(w)

    def is_verb_base(self, w):
        vf = self.verb_form(w)
        return bool(vf) and vf[1] == "base"

    def np_word(self, t, have_words, prev=None):
        """Can token t be part of a noun phrase (adjective or noun)?"""
        if (t in AUX or t in EN_PREP or t in EN_CONNECT or t in EN_DET or t in EN_POSS
                or t in EN_SUBJ or t in EN_OBJ or t in EN_Q or t in EN_NEG_WORDS
                or t in ("not", "never", "to", ",", "'s", "than", "very", "too")
                or t in LOCATION_WORDS or t in tw.ADVERBS or t in HABIT):
            return False
        if self.tr.is_adj(t):
            return True
        noun_ok = self.tr.is_noun(self.tr.lemma_noun(t)[0])
        vf = self.verb_form(t)
        if vf and not noun_ok:
            return False                          # a verb, not a noun
        if have_words and vf and not (prev and self.tr.is_adj(prev)):
            return False                          # "the dog barks": stop before the verb
        return True

    # ---- noun phrases --------------------------------------------------------------

    def parse_np(self, toks, i):
        """Noun phrase, including coordination: 'my mother and my father'."""
        np, j = self.parse_simple_np(toks, i)
        if np and j + 1 < len(toks) and toks[j][0] in ("and", "or"):
            other, k = self.parse_simple_np(toks, j + 1)
            if other and not (k < len(toks) and toks[k][0] not in AUX and self.verb_form(toks[k][0])
                              and not self.np_word(toks[k][0], True)):
                kind = "and" if toks[j][0] == "and" else "or"
                return {"raw": self.rules.connect(self.np_kreyol(np), self.np_kreyol(other), kind)}, k
        return np, j

    def parse_simple_np(self, toks, i):
        n = len(toks)
        w = lambda j: toks[j][0] if j < n else None
        if i >= n:
            return None, i
        t = w(i)
        nxt_is_np = w(i + 1) is not None and self.np_word(w(i + 1), False)
        if t in EN_SUBJ:
            return {"pron": EN_SUBJ[t]}, i + 1
        if t in EN_OBJ and not (t == "her" and nxt_is_np):
            return {"pron": EN_OBJ[t]}, i + 1
        if t in EN_REFLEXIVE:
            return {"raw": self.rules.reflexive(EN_REFLEXIVE[t])}, i + 1
        if t in EN_POSS_PRON:
            return {"raw": self.rules.possessive_pronoun(EN_POSS_PRON[t])}, i + 1
        if t in EN_STANDALONE and not nxt_is_np:
            return {"raw": EN_STANDALONE[t]}, i + 1

        np = {"det": None, "poss": None, "quant": None, "num": None, "neg": False,
              "proper": False, "words": []}
        j = i
        while j < n:
            t = w(j)
            if t in EN_DET:
                np["det"] = EN_DET[t]
            elif t in EN_POSS:
                np["poss"] = EN_POSS[t]
            elif t == "another":
                np["det"], np["quant"] = "a", "other"
            elif t in EN_QUANT and (t != "much" or np["words"]):
                np["quant"] = EN_QUANT[t]
            elif t == "no":
                np["neg"] = True
            elif t == "any":
                pass
            elif t in EN_NUM or t.isdigit():
                np["num"] = EN_NUM.get(t) or int(t)
            else:
                break
            j += 1

        intensifier = None
        while j < n:
            t, orig = toks[j]
            if t in ("very", "too", "really") and j + 1 < n and self.tr.is_adj(w(j + 1)):
                intensifier = "too" if t == "too" else "very"
                j += 1
                continue
            if orig[:1].isupper() and t not in EN_SUBJ and not (j == 0 and self.tr.knows_english(t)):
                name = [orig]
                j += 1
                while j < n and toks[j][1][:1].isupper():
                    name.append(toks[j][1])
                    j += 1
                np["words"].append((" ".join(name).casefold(), " ".join(name), None))
                np["proper"] = True
                break
            prev = np["words"][-1][0] if np["words"] else None
            if not self.np_word(t, bool(np["words"]), prev):
                break
            np["words"].append((t, orig, intensifier))
            intensifier = None
            j += 1

        if w(j) == "'s" and np["words"]:                  # John's car / my father's car
            owned, k = self.parse_simple_np(toks, j + 1)
            if owned and "words" in owned:
                owned["poss_np"] = np
                return owned, k
            return np, j + 1
        if not np["words"]:
            if np["num"]:
                return {"raw": self.rules.number(np["num"])}, j
            if np["quant"] == "all":
                return {"raw": "tout"}, j
            return None, i
        return np, j

    def np_kreyol(self, np):
        tr, R = self.tr, self.rules
        if "raw" in np:
            return np["raw"]
        if "pron" in np:
            return R.pronoun(np["pron"])
        head_lower, head_orig, head_int = np["words"][-1]
        if np["proper"]:
            noun, is_plural = (tr.kreyol_for(head_lower, "n") if head_lower in CORE else head_orig), False
        else:
            lemma, is_plural = tr.lemma_noun(head_lower)
            noun = tr.kreyol_for(lemma, "n")
        modifiers, adjectives = [], []
        for t, _, intensifier in np["words"][:-1]:
            if tr.is_adj(t):
                adj = tr.kreyol_for(tr.lemma_adj(t)[0], "adj")
                adjectives.append(R.intensify(adj, intensifier) if intensifier else adj)
            else:
                modifiers.append(tr.kreyol_for(tr.lemma_noun(t)[0], "n"))
        possessor = np["poss"] or (self.np_kreyol(np["poss_np"]) if np.get("poss_np") else None)
        det, number = np["det"], np["num"]
        if number == 1:
            det, number = "a", None
        return R.noun_phrase(noun, modifiers + adjectives, possessor=possessor, determiner=det,
                             plural=is_plural or bool(number and number > 1), number=number,
                             quantifier=np["quant"])

    # ---- complements (objects, prepositions, adverbs) --------------------------------

    def complements(self, toks, i, verb=None):
        """Translate everything after the verb. Returns (parts, adverbs, negation)."""
        tr, R = self.tr, self.rules
        n = len(toks)
        w = lambda j: toks[j][0] if j < n else None
        parts, adverbs, neg = [], [], None
        while i < n:
            t = w(i)
            if t in (",", "'s", "please", "a_lot") and t != "a_lot":
                i += 1
                continue
            if t == "not":
                neg = neg or "not"
            elif t == "never":
                neg = "never"
            elif t in EN_NEG_WORDS:
                neg = EN_NEG_WORDS[t]
            elif t == "to" and self.is_verb_base(w(i + 1)) and not (verb in MOTION and tr.is_noun(w(i + 1))):
                lemma = self.verb_form(w(i + 1))[0]
                rest, rest_adverbs, rest_neg = self.complements(toks, i + 2, lemma)
                parts.append(" ".join([tr.kreyol_for(lemma, "v")] + rest))
                adverbs += rest_adverbs
                neg = neg or rest_neg
                break
            elif t in EN_PREP:
                if w(i + 1) == "home":
                    parts.append("lakay")
                    i += 2
                    continue
                np, j = self.parse_np(toks, i + 1)
                if np:
                    parts.append(R.prepositional_phrase(EN_PREP[t], self.np_kreyol(np),
                                                        place_name=np.get("proper", False),
                                                        after_motion=verb in MOTION))
                    i = j
                    continue
            elif t in ("very", "too", "really") and tr.is_adj(w(i + 1) or ""):
                adj = tr.kreyol_for(tr.lemma_adj(w(i + 1))[0], "adj")
                parts.append(R.intensify(adj, "too" if t == "too" else "very"))
                i += 2
                continue
            elif t == "more" and tr.is_adj(w(i + 1) or "") and w(i + 2) == "than":
                np, j = self.parse_np(toks, i + 3)
                parts.append(R.comparative(tr.kreyol_for(w(i + 1), "adj"), self.np_kreyol(np) if np else ""))
                i = j
                continue
            elif tr.is_adj(t) and tr.lemma_adj(t)[1] == "comp" and w(i + 1) == "than":
                np, j = self.parse_np(toks, i + 2)
                adj = tr.kreyol_for(tr.lemma_adj(t)[0], "adj")
                parts.append(R.comparative(adj, self.np_kreyol(np) if np else ""))
                i = j
                continue
            elif t in ("and", "or"):
                parts.append("ak" if t == "and" else "oswa")
            elif (t in LOCATION_WORDS or t in HABIT or t == "a_lot"
                  or ("adv" in CORE.get(t, {}) and not self.np_word(t, False))):
                adverbs.append(tr.kreyol_for(t, "adv"))
            elif tr.is_adj(t) and not self.np_word(w(i + 1) or ",", True, t):
                parts.append(tr.kreyol_for(tr.lemma_adj(t)[0], "adj"))
            else:
                np, j = self.parse_np(toks, i)
                if np:
                    parts.append(self.np_kreyol(np))
                    if np.get("neg"):
                        neg = neg or "not"
                    i = j
                    continue
                vf = self.verb_form(t)
                parts.append(tr.kreyol_for(vf[0], "v") if vf else tr.kreyol_for(t))
            i += 1
        return parts, adverbs, neg

    # ---- clauses ----------------------------------------------------------------------

    def resolve_tense(self, aux, form, flags):
        modal = next((MODAL_TENSE[a] for a in aux if a in MODAL_TENSE), None)
        is_past = any(BE.get(a) == "past" or a in ("did", "had") for a in aux) or "past" in flags
        has_be = any(a in BE for a in aux)
        has_have = any(a in HAVE for a in aux)
        if "going" in flags:
            return "near_future"
        if "used" in flags:
            return "used_to"
        if "must" in flags:
            return "must"
        if modal:
            return modal
        if has_be and form == "ing":
            return "past_progressive" if is_past else "progressive"
        if "just" in flags:
            return "recent_past"
        if has_have and form in ("pp", "past"):
            return "past_perfect" if "had" in aux else "past"
        if "habit" in flags:
            return "used_to" if is_past or form == "past" else "habitual"
        if "done" in flags:
            return "completive"
        if is_past or form in ("past", "pp"):
            return "past"
        return "present"

    def clause(self, toks, mark):
        tr, R = self.tr, self.rules
        n = len(toks)
        w = lambda j: toks[j][0] if j < n else None
        i = 0
        please = False
        if w(i) == "please":
            please, i = True, i + 1

        # question word (and "which book" / "how many children")
        q, q_kreyol = None, None
        if w(i) in EN_Q:
            q, i = EN_Q[w(i)], i + 1
            if q in ("which", "what", "how_much", "how_many") and w(i) not in AUX and w(i) not in EN_SUBJ:
                np, j = self.parse_np(toks, i)
                if np and "words" in np:
                    word = "konbyen" if q.startswith("how") else "ki"
                    q_kreyol, i = f"{word} {self.np_kreyol(np)}", j

        aux, flags, neg = [], set(), None
        inverted = False
        if w(i) in AUX and (q or mark == "?"):
            aux.append(w(i))
            i, inverted = i + 1, True
            if w(i) == "not":
                neg, i = "not", i + 1

        subject_question = False
        if q in ("who", "what") and not q_kreyol:
            vf = self.verb_form(w(i))
            if not inverted and vf:
                subject_question = True
            elif inverted and aux[-1] in BE and vf and vf[1] == "ing":
                subject_question = True

        mode = "statement"
        if not q and not inverted:
            if w(i) == "let" and w(i + 1) == "us":
                mode, i = "lets", i + 2
            elif w(i) == "do" and w(i + 1) == "not" and self.is_verb_base(w(i + 2)):
                mode, neg, i = "imperative", "not", i + 2
            elif self.is_verb_base(w(i)) and not self.starts_clause(toks, i):
                mode = "imperative"

        subject, existential = None, False
        if mode == "statement" and not subject_question:
            if w(i) == "there" and (w(i + 1) in BE or w(i + 1) in MODAL_TENSE or (inverted and aux[-1] in BE)):
                existential, i = True, i + 1
            else:
                subject, i = self.parse_np(toks, i)

        # auxiliaries and pre-verb adverbs
        while i < n:
            t = w(i)
            if t in AUX:
                aux.append(t)
            elif t == "not":
                neg = neg or "not"
            elif t == "never":
                neg = "never"
            elif t == "just":
                flags.add("just")
            elif t in HABIT:
                flags.add("habit")
            elif t == "already":
                flags.add("done")
            elif t in ("have_to", "has_to", "had_to"):
                flags.add("must")
                if t == "had_to":
                    flags.add("past")
            elif t == "going" and w(i + 1) == "to" and self.is_verb_base(w(i + 2)) and any(a in BE for a in aux):
                flags.add("going")
                i += 1
            elif t == "used" and w(i + 1) == "to" and self.is_verb_base(w(i + 2)):
                flags.add("used")
                i += 1
            else:
                break
            i += 1

        # main verb
        verb, form = None, None
        has_be = any(a in BE for a in aux)
        vf = self.verb_form(w(i))
        if vf and not (has_be and (tr.is_adj(w(i)) or vf[1] in ("base", "s"))):
            (verb, form), i = vf, i + 1
        copula = False
        if verb is None:
            if has_be or existential:
                copula = True
            elif any(a in HAVE for a in aux):
                verb, form = "have", "base"
                aux = [a for a in aux if a not in HAVE] + (["did"] if "had" in aux else [])
            elif any(a in DO for a in aux) and not inverted:
                verb, form = "do", "base"

        passive = has_be and verb and form in ("pp", "past") and verb != "be"
        if form == "past" and any(a in HAVE for a in aux):
            form = "pp"
        tense = self.resolve_tense([a for a in aux if not (passive and a in BE and False)], form, flags)
        if passive:
            tense = "past" if any(BE.get(a) == "past" for a in aux) else "present"

        location = w(i) in EN_PREP or w(i) in LOCATION_WORDS
        adjective_predicate = w(i) is not None and (
            tr.is_adj(w(i)) or (w(i) in ("very", "too", "really", "more") and tr.is_adj(w(i + 1) or "")))
        parts, adverbs, neg2 = self.complements(toks, i, verb)
        if neg2 and (neg is None or neg == "not"):
            neg = neg2
        complement = " ".join(parts + adverbs)
        subj = None
        if subject:
            subj = subject["pron"] if "pron" in subject else self.np_kreyol(subject)
        verb_k = tr.kreyol_for(verb, "v") if verb else None
        stative = bool(verb) and (verb in tw.STATIVE_VERBS or R.is_stative(verb_k))

        def unfinish(s):
            s = s.rstrip("?.! ")
            return s[:1].lower() + s[1:]

        # questions
        if q:
            q_key = q_kreyol or q
            q_word = R.QUESTION_WORDS.get(q_key, (q_key, None))[0]
            if subject_question:
                return unfinish(R.wh_question(q_key, verb=verb_k, complement=complement, tense=tense,
                                              negation=neg, subject_question=True))
            if copula and not complement and subj:
                return unfinish(R.wh_question(q_key, subj))
            if copula:
                body = (R.there_is(complement, tense, neg) if existential else
                        R.predicate(subj, complement, self.predicate_kind(location, adjective_predicate),
                                    tense, neg))
                R._use("QST02")
                return f"{q_word} {body}"
            if not verb_k:
                return f"{q_word} {complement}".strip()
            return unfinish(R.wh_question(q_key, subj, verb_k, complement, tense, neg))

        if existential:
            body = R.there_is(complement, tense, neg)
        elif copula:
            body = R.predicate(subj or "li", complement,
                               self.predicate_kind(location, adjective_predicate), tense, neg)
        elif passive:
            body = R.impersonal_passive(verb_k, subj or "", tense)
        elif mode in ("imperative", "lets"):
            body = R.clause(None, verb_k, complement, tense=mode, negation=neg)
        elif verb_k:
            body = R.clause(subj, verb_k, complement, tense, neg, stative)
        else:
            body = " ".join(filter(None, [R.pronoun(subj) if subj in EN_SUBJ else subj, complement]))
        if inverted:
            return unfinish(R.yes_no_question(body))
        return f"tanpri, {body}" if please else body

    @staticmethod
    def predicate_kind(location, adjective):
        return "location" if location else "adjective" if adjective else "noun"


class KreyolToEnglish:
    """Read a Kreyòl sentence (markers, determiners, pronouns) and write it in English."""

    def __init__(self, translator):
        self.tr = translator
        self.rules = translator.rules

    def translate(self, text):
        text = text.strip()
        mark = text[-1] if text[-1:] in "?!." else "."
        key = re.sub(r"[^\w\s']", "", text.casefold()).strip()
        if key in KREYOL_IDIOMS:
            return KREYOL_IDIOMS[key]
        toks = self.tokenize(text)
        if not toks:
            return text
        clauses = self.split_clauses(toks)
        pieces = []
        for conn, seg in clauses:
            english = self.clause(seg, mark, conditional=conn in ("if", "when", "even if"))
            pieces.append(f"{conn} {english}" if conn else english)
        result = ", ".join(pieces) if clauses[0][0] in ("if", "when", "while", "since", "even if") \
            else " ".join(pieces)
        result = re.sub(r"\bi\b", "I", result)
        return result[:1].upper() + result[1:] + mark

    def tokenize(self, text):
        t = text.replace("’", "'").replace("'", " ")
        raw = [(w.casefold(), w) for w in re.findall(r"[^\W\d_]+|\d+|,", t)]
        out, i = [], 0
        while i < len(raw):
            for size in (2, 1):
                words = tuple(w for w, _ in raw[i:i + size])
                if len(words) == size and words in KR_PHRASES:
                    out.append((KR_PHRASES[words], " ".join(o for _, o in raw[i:i + size])))
                    i += size
                    break
            else:
                word, orig = raw[i]
                out.append((KR_NORMAL.get(word, word), orig))
                i += 1
        return out

    def split_clauses(self, toks):
        segments = [[None, []]]
        for i, tok in enumerate(toks):
            t = tok[0]
            nxt = toks[i + 1][0] if i + 1 < len(toks) else None
            if t in KR_CONNECT and (nxt in KR_PRONOUN or i == 0 or (toks[i - 1][0] == ",")):
                if not segments[-1][1]:
                    segments[-1][0] = KR_CONNECT[t]
                else:
                    segments.append([KR_CONNECT[t], []])
                continue
            if t == ",":
                if segments[-1][0] in ("if", "when", "while", "since", "even if") and nxt in KR_PRONOUN:
                    segments.append([None, []])
                continue
            segments[-1][1].append(tok)
        return [(c, s) for c, s in segments if s]

    # ---- helpers -----------------------------------------------------------------

    def verbish(self, t):
        return (t is not None and t not in KR_PRONOUN and t not in KR_DET and t not in KR_MARKERS
                and (self.tr.kreyol_has(t, "v") or self.tr.kreyol_has(t, "adj")))

    def parse_np(self, toks, i):
        n = len(toks)
        w = lambda j: toks[j][0] if j < n else None
        np = {"det": None, "quant": None, "num": None, "pre": [], "post": [], "head": None}
        j = i
        while j < n:
            t = w(j)
            if t == "yon":
                np["det"] = "a"
            elif t in KR_QUANT and w(j + 1) is not None:
                np["quant"] = KR_QUANT[t]
            elif t in KR_NUM:
                np["num"] = KR_NUM[t]
            elif t in self.rules.BANGS and w(j + 1) not in (None, *KR_DET):
                np["pre"].append(t)
            else:
                break
            j += 1
        t = w(j)
        if t is None or t in KR_MARKERS or t in KR_CONNECT or t.startswith("?") or t in ("se", "ki", ","):
            return None, i
        if t in KR_PRONOUN:
            return {"pron": KR_PRONOUN[t]}, j + 1
        if t in ("#this", "#these", "#that"):
            return {"raw": t[1:]}, j + 1
        np["head"] = toks[j]
        j += 1
        k, found = j, None
        while k < n and k - j < 4:
            t = w(k)
            if t in KR_DET:
                found = k
                break
            if t in KR_MARKERS or t in KR_PREP or t.startswith(("?", "@")) or t in (",", "se", "ki"):
                break
            k += 1
        if found is not None:
            np["post"] = toks[j:found]
            np["det"] = KR_DET[w(found)]
            return np, found + 1
        while j < n:
            t = w(j)
            if t in KR_PRONOUN or (self.tr.kreyol_has(t, "adj") and not self.tr.kreyol_has(t, "v")):
                np["post"].append(toks[j])
                j += 1
            else:
                break
        return np, j

    def np_english(self, np, role="obj"):
        tr = self.tr
        if "pron" in np:
            return (EN_SUBJ_FORM if role == "subj" else EN_OBJ_FORM)[np["pron"]]
        if "raw" in np:
            return np["raw"]
        head, orig = np["head"]
        proper = orig[:1].isupper() and head not in tr.kreyol_to_eng and head not in KREYOL_CORE
        noun = orig if proper else tr.english_for(head, "n")
        is_plural = np["det"] in ("pl", "these") or bool(np["num"] and np["num"] > 1)
        if is_plural and not proper:
            noun = plural(noun)
        adjectives = [tr.english_for(a, "adj") for a in np["pre"]]
        owner, owner_pron = None, None
        for t, o in np["post"]:
            if t in KR_PRONOUN:
                owner_pron = KR_PRONOUN[t]
            elif tr.kreyol_has(t, "adj") and not tr.kreyol_has(t, "n"):
                adjectives.append(tr.english_for(t, "adj"))
            else:
                owner = o if o[:1].isupper() else tr.english_for(t, "n")
        words, after, det = [], [], np["det"]
        if np["quant"]:
            words.append(np["quant"])
        if det in ("this", "these") and (owner or owner_pron):
            words.append(det)                     # liv mwen sa a -> this book of mine
            after = ["of", f"{owner}'s" if owner else EN_POSS_PRON_FORM[owner_pron]]
            owner = owner_pron = det = None
        if owner:
            words.append((f"{EN_POSS_FORM[owner_pron]} {owner}'s" if owner_pron else f"{owner}'s"))
        elif owner_pron:
            words.append(EN_POSS_FORM[owner_pron])
        elif det in ("the", "pl"):
            words.append("the")
        elif det in ("this", "these"):
            words.append(det)
        if np["num"]:
            words.append(EN_NUM_WORD.get(np["num"], str(np["num"])))
        phrase = " ".join(adjectives + [noun])
        if np["det"] == "a" and not owner and not owner_pron:
            phrase = with_article(phrase)
        return " ".join(words + [phrase] + after)

    def agreement(self, np):
        if not np:
            return "3s"
        if "pron" in np:
            return AGREEMENT.get(np["pron"], "pl")
        if np.get("det") in ("pl", "these") or (np.get("num") or 0) > 1:
            return "pl"
        return "3s"

    def complements(self, toks, i):
        tr = self.tr
        n = len(toks)
        w = lambda j: toks[j][0] if j < n else None
        out, adverbs, end_neg = [], [], []
        while i < n:
            t, orig = toks[i]
            if t == ",":
                i += 1
            elif t in KR_END_NEG:
                end_neg.append(t)
                i += 1
            elif t.startswith("@"):
                adverbs.append(t[1:])
                i += 1
            elif t in KR_PRONOUN:
                out.append(EN_OBJ_FORM[KR_PRONOUN[t]])
                i += 1
            elif t in KR_LOCATION and (i + 1 >= n or t != "lakay"):
                out.append(KR_LOCATION[t])
                i += 1
            elif t in ("ak", "avèk", "e") and out and w(i + 1) is not None:
                np, j = self.parse_np(toks, i + 1)       # diri ak pwa -> rice and beans
                if np:
                    out.append("and " + self.np_english(np))
                    i = j
                else:
                    i += 1
            elif t in KR_PREP:
                np, j = self.parse_np(toks, i + 1)
                if t == "lakay" and np:
                    out.append(f"at {self.np_english(np)}'s house")
                elif np:
                    out.append(f"{KR_PREP[t]} {self.np_english(np)}")
                else:
                    out.append(KR_PREP[t])
                i = j if np else i + 1
            elif t in ("trè", "twò") and w(i + 1):
                out.append(("very " if t == "trè" else "too ") + tr.english_for(w(i + 1), "adj"))
                i += 2
            elif t == "pi" and w(i + 1):
                adj = tr.english_for(w(i + 1), "adj")
                out.append("better" if adj == "good" else "worse" if adj == "bad" else f"more {adj}")
                i += 2
            elif t == "pase":
                out.append("than")
                i += 1
            elif "adv" in KREYOL_CORE.get(t, {}):
                adverbs.append(KREYOL_CORE[t]["adv"])
                i += 1
            else:
                np, j = self.parse_np(toks, i)
                if np:
                    out.append(self.np_english(np))
                    i = j
                else:
                    out.append(tr.english_for(t) if t in tr.kreyol_to_eng or t in KREYOL_CORE else orig)
                    i += 1
        return out, adverbs, end_neg

    # ---- clauses ------------------------------------------------------------------

    def clause(self, toks, mark, conditional=False):
        tr, R = self.tr, self.rules
        n = len(toks)
        w = lambda j: toks[j][0] if j < n else None
        i = 0
        yes_no = q = None
        q_np = None
        if w(i) == "èske":
            yes_no, i = True, i + 1
        if w(i) and w(i).startswith("?"):
            q, i = w(i)[1:], i + 1
        elif w(i) == "ki" and i == 0 and w(i + 1) not in (None, *KR_PRONOUN):
            np, j = self.parse_np(toks, i + 1)
            if np:
                q, q_np, i = "which", np, j
        subject_question = False
        if q and w(i) == "ki":
            subject_question, i = True, i + 1

        mode, subject, existential = "statement", None, False
        if w(i) == "ann":
            mode, i = "lets", i + 1
        elif not subject_question:
            if w(i) in KR_PRONOUN:
                subject, i = {"pron": KR_PRONOUN[w(i)]}, i + 1
            elif w(i) in KR_MARKERS or w(i) in ("gen", "genyen"):
                pass
            elif (tr.kreyol_has(w(i), "v") and not tr.kreyol_has(w(i), "n")
                  and w(i) not in R.BANGS and w(i + 1) not in KR_DET):
                mode = "imperative"
            else:
                subject, i = self.parse_np(toks, i)

        neg, markers = None, []
        while i < n:
            t = w(i)
            if t == "pa":
                neg = neg or "not"
            elif t == "poko":
                neg = "not_yet"
            elif t == "janm":
                neg = "never"
            elif t in ("te", "ap", "va", "pral", "ta"):
                markers.append(t)
            elif t == "a" and (subject and "pron" in subject or markers or neg) and self.verbish(w(i + 1)):
                markers.append("va")
            elif t in ("fèk", "sot", "fin", "konn", "dwe", "ka", "kapab", "vin") and self.verbish(w(i + 1)):
                markers.append(t)
            else:
                break
            i += 1
        if mode == "statement" and subject is None and not subject_question and w(i) not in ("gen", "genyen"):
            if neg and self.verbish(w(i)):
                mode = "imperative"

        # predicate
        t = w(i)
        lemma, kind, infinitive = None, None, []
        if t == "se":
            kind, i = "noun", i + 1
        elif t in ("gen", "genyen"):
            lemma, i = "have", i + 1
            existential = subject is None and mode == "statement"
        elif t == "ye":
            kind, i = "none", i + 1
        elif t is None:
            kind = "none"
        elif t in KR_LOCATION or t in KR_PREP:
            kind = "location"
        elif tr.kreyol_has(t, "v") or (mode != "statement" and t not in KR_DET):
            lemma, i = tr.english_for(t, "v"), i + 1
            while self.verbish(w(i)) and tr.kreyol_has(w(i), "v") and w(i + 1) not in KR_DET:
                infinitive.append("to " + tr.english_for(w(i), "v"))
                i += 1
        elif tr.kreyol_has(t, "adj"):
            kind = "adjective"
        else:
            kind = "noun"

        predicate = []
        if kind == "adjective":
            predicate, i = [tr.english_for(t, "adj")], i + 1
        rest, adverbs, end_neg = self.complements(toks, i)
        rest = predicate + rest
        if kind == "noun" and not ("pral" in markers or "ap" in markers) and rest and not rest[0].split()[0] in ("the", "a", "an", "my", "your",
                                                                   "his/her", "our", "their", "this", "these"):
            rest[0] = with_article(rest[0])

        # tense, aspect and mood from the markers
        stative = kind is not None or (lemma and (lemma in tw.STATIVE_VERBS or lemma in ("have", "cost")))
        if "vin" in markers and kind == "adjective":
            lemma, kind, stative = "become", None, False
        elif "vin" in markers and lemma:
            infinitive.insert(0, "to " + lemma)
            lemma = "come"
        if lemma is None and kind in ("noun", "location") and ("pral" in markers or "ap" in markers):
            lemma, kind = "go", None                 # Nou pral lekòl -> We are going to school
            markers = [m for m in markers if m != "pral"] + ["ap"]
            if rest and not rest[0].startswith(("in ", "at ", "to ")):
                rest[0] = "to " + re.sub(r"^(a|an) ", "", rest[0])
        if lemma is None:
            lemma = "be"
        modal = prog = going = used = False
        adv = None
        tense = "present"
        if "ta" in markers:
            modal = "should" if "dwe" in markers else "would"
        elif "va" in markers:
            modal = "will"
        elif "pral" in markers:
            going = True
        elif "ap" in markers:
            prog = True
            tense = "past" if "te" in markers else "present"
        if not modal and "dwe" in markers:
            modal = "must"
        if not modal and ("ka" in markers or "kapab" in markers):
            modal = "could" if "te" in markers else "can"
        if "konn" in markers:
            if "te" in markers:
                used = True
            else:
                adv = "usually"
        if "fèk" in markers or "sot" in markers:
            adv, tense = "just", "past"
        if "fin" in markers:
            adv, tense = "already", "past"
        if not (modal or prog or going or used or adv):
            tense = "past" if "te" in markers or (not stative and not conditional) else "present"

        negative = neg in ("not", "not_yet")
        never = neg == "never"
        agr = self.agreement(subject)
        if subject_question:
            agr = "3s"
        words, has_aux = english_vp(lemma, agr, tense, modal, prog, going, used, adv,
                                    negative, never, question=bool((q and not subject_question) or yes_no))
        if neg == "not_yet" and not (modal or prog or going or used) and lemma != "be":
            words, has_aux = ["has" if agr == "3s" else "have", "not", inflect_first(lemma, past_participle)], True
        end = []
        for word in end_neg:
            end.append(KR_END_NEG[word][0 if (negative or never) else 1])
        if neg == "not_yet":
            end.append("yet")
        tail = infinitive + rest + adverbs + end

        if existential:
            np_text = " ".join(rest) or "something"
            if negative:
                np_text = re.sub(r"^(a|an|the) ", "", np_text)
                return " ".join(["there", be_form("3s", tense), "no", np_text] + adverbs)
            return " ".join(["there", be_form("3s", tense), np_text] + adverbs)
        if kind == "none" and not q and not yes_no and not tail and subject:
            return self.np_english(subject, "subj")      # just a noun phrase
        if mode == "imperative":
            return " ".join((["do", "not"] if negative else ["never"] if never else []) + [lemma] + tail)
        if mode == "lets":
            return " ".join(["let's"] + (["not"] if negative else []) + [lemma] + tail)

        subj_text = self.np_english(subject, "subj") if subject else ""
        if q:
            q_text = Q_ENGLISH.get(q, q)
            if q_np:
                q_text = f"which {self.np_english(q_np)}".replace("which the ", "which ")
            if subject_question:
                return " ".join([q_text] + words + tail)
            if has_aux:
                return " ".join([q_text, words[0], subj_text] + words[1:] + tail)
            return " ".join([q_text, subj_text] + words + tail)
        if yes_no and has_aux:
            return " ".join([words[0], subj_text] + words[1:] + tail)
        return " ".join(filter(None, [subj_text] + words + tail))


def main():
    translator = Translator()
    print("Type a word or a sentence (English or Kreyòl). Press Enter on an empty line to quit.")
    while True:
        text = input("> ").strip()
        if text == "":
            break
        if len(text.split()) == 1 and text[-1] not in "?!.":
            result = translator.lookup(text)
            print(", ".join(f"{w} ({t.rstrip('?')})" if t else w for w, t in result)
                  if result else "word not found")
            continue
        result, source = translator.translate_sentence(text)
        print(result)
        rules = translator.explain()
        if source == "english" and rules:
            print("  rules:", ", ".join(rule_id for rule_id, _ in rules))


if __name__ == "__main__":
    main()
