import csv
from pathlib import Path

VOWELS = set("aeiouèòàéì")


class SentenceRules:
    """Builds Haitian Kreyòl phrases and sentences from the rules in rulelist.csv.

    Every builder works on Kreyòl words and records the rule ids it used,
    so explain() can show which rules produced the last result.
    """

    # BANGS adjectives go before the noun. Value = sort order when several stack (BANGS07).
    BANGS = {
        "premye": 0, "dezyèm": 0, "twazyèm": 0, "dènye": 0,      # Number
        "bèl": 1, "lèd": 1, "bon": 1, "move": 1,                 # Beauty / Goodness
        "jenn": 2, "vye": 2, "vyèy": 2, "nouvo": 2,              # Age
        "gwo": 3, "gran": 3, "ti": 3, "piti": 3,                 # Size
    }

    # English key -> (long form, short form)
    PRONOUNS = {
        "i": ("mwen", "m"), "you": ("ou", "w"), "he": ("li", "l"), "she": ("li", "l"),
        "it": ("li", "l"), "we": ("nou", "n"), "you_pl": ("nou", "n"), "they": ("yo", "y"),
    }
    SHORT_PRONOUN = {"mwen": "m", "ou": "w", "li": "l", "nou": "n", "yo": "y"}

    NUMBERS = {1: "yon", 2: "de", 3: "twa", 4: "kat", 5: "senk",
               6: "sis", 7: "sèt", 8: "uit", 9: "nèf", 10: "dis"}

    QUANTIFIERS = {
        "each": "chak", "every": "chak", "all": "tout", "some": "kèk", "several": "plizyè",
        "many": "anpil", "no": "okenn", "other": "lòt", "same": "menm", "enough": "ase",
    }
    QUANTIFIER_RULE = {"chak": "DETR01", "tout": "DETR02", "kèk": "DETR03", "plizyè": "DETR04",
                       "anpil": "DETR05", "okenn": "DETR06", "lòt": "DETR07", "menm": "DETR08",
                       "ase": "DETR09"}

    STATIVE_VERBS = {"konnen", "konn", "renmen", "vle", "genyen", "gen", "bezwen",
                     "sanble", "rayi", "kwè", "konprann", "ye", "dwe", "kapab", "ka"}

    # Full form -> short form used when something follows the verb (ORD07)
    SHORT_VERBS = {"ale": "al", "vini": "vin", "konnen": "konn", "kapab": "ka", "rete": "ret"}

    # tense name -> marker slots (anterior, aspect/mood, habitual/completive, modal) and rule id
    TENSES = {
        "present":          ({}, "TNS02"),
        "past":             ({}, "TNS01"),                       # stative verbs get 'te' (TNS03)
        "past_perfect":     ({"ant": "te"}, "TNS03"),
        "progressive":      ({"asp": "ap"}, "TNS04"),
        "definite_future":  ({"asp": "ap"}, "TNS05"),
        "future":           ({"asp": "va"}, "TNS06"),
        "near_future":      ({"asp": "pral"}, "TNS07"),
        "past_progressive": ({"ant": "te", "asp": "ap"}, "TNS08"),
        "conditional":      ({"asp": "ta"}, "TNS09"),
        "should":           ({"asp": "ta", "modal": "dwe"}, "TNS10"),
        "recent_past":      ({"hab": "fèk"}, "TNS11"),
        "habitual":         ({"hab": "konn"}, "TNS12"),
        "used_to":          ({"ant": "te", "hab": "konn"}, "TNS13"),
        "must":             ({"modal": "dwe"}, "TNS14"),
        "can":              ({"modal": "ka"}, "TNS15"),
        "could":            ({"ant": "te", "modal": "ka"}, "TNS15"),
        "become":           ({"hab": "vin"}, "TNS16"),
        "completive":       ({"hab": "fin"}, "TNS17"),
        "imperative":       ({}, "TNS18"),
        "lets":             ({}, "TNS19"),
    }

    # negation type -> (word replacing/after 'pa', word placed at the end, rule id)
    NEGATIONS = {
        "not":        ("pa", "", "NEG01"),
        "never":      ("pa", "", "NEG02"),        # 'janm' goes right before the verb
        "anymore":    ("pa", "ankò", "NEG03"),
        "nothing":    ("pa", "anyen", "NEG04"),
        "nobody":     ("pa", "pèsonn", "NEG05"),
        "not_yet":    ("poko", "", "NEG06"),
        "not_at_all": ("pa", "ditou", "NEG07"),
    }

    QUESTION_WORDS = {
        "what": ("kisa", "QST03"), "who": ("ki moun", "QST04"), "where": ("kote", "QST06"),
        "when": ("kilè", "QST07"), "how": ("kouman", "QST08"), "why": ("poukisa", "QST09"),
        "how_much": ("konbyen", "QST10"), "how_many": ("konbyen", "QST10"), "which": ("ki", "QST11"),
    }

    CONNECTORS = {
        "and": ("ak", "CON01"), "and_then": ("epi", "CON02"), "but": ("men", "CON03"),
        "or": ("oswa", "CON04"), "because": ("paske", "CON05"), "so": ("donk", "CON06"),
        "if": ("si", "CON07"), "when": ("lè", "CON08"), "while": ("pandan", "CON09"),
        "even_if": ("menmsi", "CON10"), "so_that": ("pou", "CON11"), "that": ("ke", "CON14"),
        "since": ("kòm", "CON15"),
    }

    PREPOSITIONS = {
        "in": ("nan", "PREP01"), "at": ("nan", "PREP01"), "to": ("nan", "PREP01"),
        "on": ("sou", "PREP02"), "about": ("sou", "PREP02"), "under": ("anba", "PREP03"),
        "above": ("anwo", "PREP04"), "in_front_of": ("devan", "PREP05"), "behind": ("dèyè", "PREP06"),
        "beside": ("bò kote", "PREP07"), "with": ("ak", "PREP08"), "for": ("pou", "PREP09"),
        "from": ("soti", "PREP10"), "at_home": ("lakay", "PREP11"), "at_place_of": ("kot", "PREP12"),
        "inside": ("anndan", "PREP13"), "outside": ("deyò", "PREP13"), "between": ("ant", "PREP14"),
        "before": ("anvan", "PREP15"), "after": ("apre", "PREP15"), "without": ("san", "PREP16"),
        "until": ("jis", "PREP17"), "against": ("kont", "PREP18"),
    }

    INTENSIFIERS = {"very": "trè", "too": "twò"}

    def __init__(self, path=Path(__file__).with_name("rulelist.csv")):
        self.rules = {}
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                self.rules[row["id"]] = row
        self.article_exceptions = {}   # word -> article, overrides THE02-THE06
        self.applied = []

    # ---- bookkeeping -------------------------------------------------------

    def _use(self, *rule_ids):
        for rule_id in rule_ids:
            if rule_id not in self.applied:
                self.applied.append(rule_id)

    def explain(self, clear=True):
        """Return [(rule id, rule text)] for the rules used since the last clear."""
        result = [(r, self.rules[r]["rule"] if r in self.rules else "") for r in self.applied]
        if clear:
            self.applied = []
        return result

    @staticmethod
    def finish(text, mark="."):
        """Capitalize and punctuate a sentence."""
        text = " ".join(text.split())
        return text[:1].upper() + text[1:] + mark if text else text

    # ---- "the" rules -------------------------------------------------------

    def rule_the(self, word, plural=False):
        """Return the definite article that follows `word` (la / a / an / nan / yo)."""
        if plural:
            self._use("THE07")
            return "yo"
        w = word.strip().split()[-1].casefold() if word.strip() else ""
        if w in self.article_exceptions:
            return self.article_exceptions[w]
        if not w:
            return "la"
        if w[-1] in "mn":
            # an/en/on with a single final n is a nasal vowel; anything else is a nasal consonant
            if w.endswith(("an", "en", "on")) and not w.endswith(("ann", "enn", "onn")):
                self._use("THE04")
                return "an"
            self._use("THE06")
            return "nan"
        if w[-1] in VOWELS:
            stem = w.rstrip("".join(VOWELS))
            if stem and stem[-1] in "mn":
                self._use("THE05")
                return "an"
            self._use("THE03")
            return "a"
        self._use("THE02")
        return "la"

    def definite(self, phrase, plural=False):
        """Attach the definite article to the end of a whole phrase (THE01, THE10)."""
        self._use("THE01", "THE10")
        return f"{phrase} {self.rule_the(phrase, plural)}"

    def indefinite(self, phrase):
        self._use("THE08")
        return f"yon {phrase}"

    # ---- BANGS / adjectives / nouns ----------------------------------------

    def is_bangs(self, adjective):
        return adjective.casefold() in self.BANGS

    def place_adjectives(self, noun, adjectives):
        """BANGS adjectives before the noun, every other adjective after it."""
        before = sorted((a for a in adjectives if self.is_bangs(a)), key=lambda a: self.BANGS[a.casefold()])
        after = [a for a in adjectives if not self.is_bangs(a)]
        if before:
            self._use("BANGS01")
            if len(before) > 1 or after:
                self._use("BANGS07")
        if after:
            self._use("ADJ01")
        return " ".join(before + [noun] + after)

    def number(self, n):
        self._use("BANGS04")
        return self.NUMBERS.get(n, str(n))

    def noun_phrase(self, noun, adjectives=(), possessor=None, determiner=None,
                    plural=False, number=None, quantifier=None):
        """Build a noun phrase in the NOUN08 order:
        yon/QUANT + BANGS + NOUN + ADJ + POSSESSOR + DEMONSTRATIVE/ARTICLE + yo

        determiner: None, "the", "a", "this"/"that" (sa a), "these"/"those" (sa yo)
        """
        self._use("NOUN08")
        parts = []
        if determiner == "a":
            self._use("THE08")
            parts.append("yon")
        if quantifier:
            q = self.QUANTIFIERS.get(quantifier, quantifier)
            self._use(self.QUANTIFIER_RULE.get(q, "DETR01"))
            parts.append(q)
        if number is not None:
            parts.append(self.number(number))
            self._use("NOUN02")
        parts.append(self.place_adjectives(noun, adjectives))
        if possessor:
            parts.append(self._possessor(possessor))
        phrase = " ".join(parts)

        if determiner == "the":
            return self.definite(phrase, plural)
        if determiner in ("this", "that", "these", "those"):
            return self.demonstrative(phrase, plural or determiner in ("these", "those"))
        if plural and possessor:
            self._use("THE07")
            return f"{phrase} yo"
        if plural and number is None:
            self._use("THE09", "NOUN02")
        return phrase

    def _possessor(self, owner):
        key = owner.casefold()
        if key in self.PRONOUNS or key in self.SHORT_PRONOUN:
            self._use("PRON08")
            return self.pronoun(owner)
        self._use("NOUN04")
        return owner

    def compound(self, head, modifier):
        self._use("NOUN06")
        return f"{head} {modifier}"

    def gendered(self, noun, male):
        self._use("NOUN03")
        return f"{noun} {'gason' if male else 'fi'}"

    def comparative(self, adjective, than):
        self._use("ADJ05")
        word = self._irregular_comparative(adjective)
        return f"{word} pase {than}"

    def superlative(self, adjective, group=None):
        self._use("ADJ06")
        word = self._irregular_comparative(adjective)
        return f"{word} nan {group}" if group else word

    def _irregular_comparative(self, adjective):
        if adjective in ("bon", "move"):
            self._use("ADJ10")
            return "pi bon" if adjective == "bon" else "pi mal"
        return f"pi {adjective}"

    def equal(self, adjective, other):
        self._use("ADJ07")
        return f"osi {adjective} tankou {other}"

    def intensify(self, adjective, how="very"):
        """very/too -> before, a_lot -> 'anpil' after, repeat -> reduplication."""
        if how == "a_lot":
            self._use("ADJ08")
            return f"{adjective} anpil"
        if how == "repeat":
            self._use("ADJ09")
            return f"{adjective} {adjective}"
        self._use("ADJ08")
        return f"{self.INTENSIFIERS.get(how, how)} {adjective}"

    # ---- pronouns ----------------------------------------------------------

    def pronoun(self, person, short=False):
        """English key (i, you, he, we, you_pl, they...) or Kreyòl pronoun -> Kreyòl form."""
        key = person.casefold()
        if key in self.PRONOUNS:
            long_form, short_form = self.PRONOUNS[key]
        elif key in self.SHORT_PRONOUN:
            long_form, short_form = key, self.SHORT_PRONOUN[key]
        else:
            return person
        self._use({"mwen": "PRON01", "ou": "PRON02", "li": "PRON03", "yo": "PRON06"}.get(
            long_form, "PRON05" if key == "you_pl" else "PRON04"))
        if short:
            self._use("PRON13", "CTR01")
            return short_form
        return long_form

    def is_pronoun(self, word):
        w = word.casefold()
        return w in self.SHORT_PRONOUN or w in self.SHORT_PRONOUN.values()

    def possessive(self, noun, owner, definite=False, plural=False):
        """liv mwen / liv mwen an / liv mwen yo (PRON08, PRON09)."""
        if definite or plural:
            self._use("PRON09")
        return self.noun_phrase(noun, possessor=owner, determiner="the" if definite else None,
                                plural=plural)

    def possessive_pronoun(self, owner):
        """mine/yours/... -> pa m / pa w / pa l / pa nou / pa yo"""
        self._use("PRON10")
        long_form = self.pronoun(owner)
        return f"pa {self.SHORT_PRONOUN[long_form] if long_form in ('mwen', 'ou', 'li') else long_form}"

    def reflexive(self, owner):
        self._use("PRON11")
        return f"tèt {self.pronoun(owner)}"

    def emphatic(self, person):
        self._use("PRON12")
        return f"{self.pronoun(person)} menm"

    def impersonal_passive(self, verb, obj, tense="past"):
        """English passive 'X was VERBed' -> 'Yo VERB X' (PRON14)."""
        self._use("PRON14")
        return self.clause("yo", verb, obj, tense=tense)

    # ---- demonstratives ----------------------------------------------------

    def demonstrative(self, phrase, plural=False, far=False):
        """liv sa a (this/that), liv sa yo (these/those); far adds 'la' (DEM04)."""
        self._use("DEM06")
        if plural:
            self._use("DEM02")
            result = f"{phrase} sa yo"
        else:
            self._use("DEM01")
            result = f"{phrase} sa a"
        if far:
            self._use("DEM04")
            result += " la"
        return result

    # ---- tense / marker order / negation -----------------------------------

    def is_stative(self, verb):
        return verb.casefold() in self.STATIVE_VERBS

    def markers(self, tense="present", stative=False, negation=None):
        """Return the ordered pre-verbal words for a tense + negation (ORD01-ORD05)."""
        if tense not in self.TENSES:
            raise ValueError(f"unknown tense {tense!r}; choose from {', '.join(self.TENSES)}")
        slots, rule_id = self.TENSES[tense]
        slots = dict(slots)
        self._use(rule_id)
        if tense == "past" and stative:
            self._use("TNS03")
            slots["ant"] = "te"

        neg_word = None
        if negation:
            neg_word, _, neg_rule = self.NEGATIONS[negation]
            self._use(neg_rule)
            if slots.get("asp") == "va":           # future is negated with p ap, not pa va
                self._use("ORD04")
                slots["asp"] = "ap"
        if slots.get("ant") == "te" and slots.get("asp") in ("va", "a"):
            self._use("ORD03")
            slots.pop("ant")
            slots["asp"] = "ta"

        words = [w for w in (neg_word, slots.get("ant"), slots.get("asp"),
                             slots.get("hab"), slots.get("modal")) if w]
        if negation == "never":
            words.append("janm")
        if len(words) > 1:
            self._use("ORD01")
        return self._contract_markers(words)

    def _contract_markers(self, words):
        out = []
        for i, w in enumerate(words):
            nxt = words[i + 1] if i + 1 < len(words) else ""
            if w == "te" and nxt[:1] in VOWELS:
                self._use("ORD02" if nxt == "ap" else "ORD05", "CTR03")
                w = "t"
            elif w == "pa" and nxt == "ap":
                self._use("ORD04", "CTR04")
                w = "p"
            out.append(w)
        return out

    def short_verb(self, verb, followed=True):
        """Use al / vin / konn / ka / ret when something follows the verb (ORD07)."""
        if followed and verb in self.SHORT_VERBS:
            self._use("ORD07")
            return self.SHORT_VERBS[verb]
        return verb

    def clause(self, subject, verb, complement="", tense="present", negation=None,
               stative=None, contract=True):
        """SUBJ + (pa) + markers + VERB + complement + (negation end word).

        negation: not, never, anymore, nothing, nobody, not_yet, not_at_all
        subject may be None for imperatives; tense "lets" gives 'Ann + VERB'.
        """
        stative = self.is_stative(verb) if stative is None else stative
        end_word = self.NEGATIONS[negation][1] if negation else ""

        if tense in ("imperative", "lets"):
            self.markers(tense)
            head = ["pa"] if negation else []
            if negation:
                self._use("NEG10")
            if tense == "lets":
                head.insert(0, "ann")
            pre = head
            subject = None
        else:
            pre = self.markers(tense, stative, negation)

        if complement and contract and complement in self.SHORT_PRONOUN and verb[-1:] in VOWELS:
            self._use("CTR02", "PRON07")
            complement = self.SHORT_PRONOUN[complement]
        elif complement and complement.casefold() in self.SHORT_PRONOUN:
            self._use("PRON07")

        followed = bool(complement or end_word)
        words = pre + [self.short_verb(verb, followed)]
        if subject:
            subject = self.pronoun(subject) if subject.casefold() in self.PRONOUNS else subject
            first = words[0]
            if contract and subject in self.SHORT_PRONOUN and first[:1] in VOWELS:
                if first == "va":
                    words[0] = "a"
                self._use("PRON13", "CTR01", "ORD06")
                subject = self.SHORT_PRONOUN[subject]
            elif contract and subject in self.SHORT_PRONOUN and first == "va":
                self._use("TNS06")
                words[0] = "a"
                subject = self.SHORT_PRONOUN[subject]
            words.insert(0, subject)
        if complement:
            words.append(complement)
        if end_word:
            words.append(end_word)
        return " ".join(words)

    def nobody_did(self, verb, complement="", tense="past"):
        """Pèsonn pa VERB (nobody as subject, NEG05)."""
        self._use("NEG05")
        return "pèsonn " + self.clause(None, verb, complement, tense, negation="not")

    def neither_nor(self, subject, verb, first, second, tense="present"):
        self._use("NEG08")
        return self.clause(subject, verb, f"ni {first} ni {second}", tense, negation="not")

    # ---- copula / existential / focus --------------------------------------

    def predicate(self, subject, predicate, kind="noun", tense="present", negation=None):
        """'to be' sentences.

        kind="noun"      -> Li se doktè   (se dropped when a marker or pa is present)
        kind="adjective" -> Li bèl        (no copula, ADJ03 / COP02)
        kind="location"  -> Li lakay      (no copula, COP03)
        """
        if kind == "noun":
            self._use("COP01")
            if tense == "present" and not negation:
                return self.clause(subject, "se", predicate, stative=True)
            return self.clause(subject, predicate, tense=tense, negation=negation, stative=True)
        self._use("ADJ03", "COP02" if kind == "adjective" else "COP03")
        if tense != "present":
            self._use("ADJ04")
        return self.clause(subject, predicate, tense=tense, negation=negation, stative=True)

    def it_is(self, thing):
        self._use("COP05")
        return f"se {thing}"

    def there_is(self, phrase, tense="present", negation=None):
        """Gen ... / Pa gen ... / Te gen ... (COP06, NEG09)."""
        self._use("COP06")
        if negation:
            self._use("NEG09")
        return self.clause(None, "gen", phrase, tense=tense, negation=negation, stative=True)

    def focus(self, subject, verb_phrase):
        """Se Jan ki vini (COP07)."""
        self._use("COP07")
        return f"se {subject} {self._ki(verb_phrase)}"

    def predicate_cleft(self, subject, verb, tense="past"):
        """Se kouri li kouri (COP08)."""
        self._use("COP08")
        return f"se {verb} {self.clause(subject, verb, tense=tense)}"

    def _ki(self, rest):
        if rest[:1] in VOWELS:
            self._use("CTR06")
            return f"k {rest}"
        return f"ki {rest}"

    # ---- questions ---------------------------------------------------------

    def yes_no_question(self, statement):
        self._use("QST01")
        return self.finish(f"èske {statement}", "?")

    def wh_question(self, qword, subject=None, verb=None, complement="", tense="present",
                    negation=None, subject_question=False):
        """Question words go first (QST02).

        subject_question=True -> Ki moun ki vini?  (QST05)
        verb=None             -> Kouman ou ye?     (COP04 / QST12)
        """
        word, rule_id = self.QUESTION_WORDS.get(qword, (qword, "QST02"))
        self._use("QST02", rule_id)
        if subject_question:
            self._use("QST05")
            rest = self.clause(None, verb, complement, tense, negation)
            return self.finish(f"{word} {self._ki(rest)}", "?")
        if verb is None:
            self._use("COP04", "QST12")
            subj = self.pronoun(subject) if subject.casefold() in self.PRONOUNS else subject
            return self.finish(f"{word} {subj} ye", "?")
        return self.finish(f"{word} {self.clause(subject, verb, complement, tense, negation)}", "?")

    def tag_question(self, statement):
        self._use("QST13")
        return self.finish(f"{statement}, pa vre", "?")

    # ---- connections / relative clauses ------------------------------------

    def connect(self, left, right, kind="and_then"):
        """kind: and (nouns), and_then (clauses), but, or, because, so, if, when, while,
        even_if, so_that, that, since."""
        word, rule_id = self.CONNECTORS[kind]
        self._use(rule_id)
        if kind in ("if", "when", "while", "even_if", "since"):
            return f"{word} {left}, {right}"
        return f"{left} {word} {right}"

    def relative(self, noun, clause, subject_relative=True, determiner="the"):
        """moun ki vini an (CON12 + THE11), liv mwen li a (CON13)."""
        if subject_relative:
            self._use("CON12")
            phrase = f"{noun} {self._ki(clause)}"
        else:
            self._use("CON13")
            phrase = f"{noun} {clause}"
        if determiner == "the":
            self._use("THE11")
            return f"{phrase} {self.rule_the(phrase)}"
        if determiner in ("this", "that"):
            return self.demonstrative(phrase)
        return phrase

    # ---- prepositions ------------------------------------------------------

    def prepositional_phrase(self, prep, phrase, place_name=False, after_motion=False):
        """prep is an English key (in, on, under, with, ...) or a Kreyòl word.
        'to' + a place name after a motion verb takes no preposition (PREP19)."""
        if prep == "to" and (place_name or after_motion):
            self._use("PREP19")
            return phrase
        word, rule_id = self.PREPOSITIONS.get(prep, (prep, None))
        if rule_id:
            self._use(rule_id)
        if prep == "between" and isinstance(phrase, (tuple, list)):
            return f"ant {phrase[0]} ak {phrase[1]}"
        return f"{word} {phrase}"

    # ---- full sentence -----------------------------------------------------

    def kreyol_sentence(self, subject, verb, complement="", tense="present", negation=None,
                        question=None, contract=True):
        """One-call sentence builder.

        question: None, "yes_no", "tag", or a question word key (what, who, where, ...).
        """
        if question == "yes_no":
            return self.yes_no_question(self.clause(subject, verb, complement, tense, negation,
                                                    contract=contract))
        if question == "tag":
            return self.tag_question(self.clause(subject, verb, complement, tense, negation,
                                                 contract=contract))
        if question:
            return self.wh_question(question, subject, verb, complement, tense, negation)
        mark = "!" if tense in ("imperative", "lets") else "."
        return self.finish(self.clause(subject, verb, complement, tense, negation,
                                       contract=contract), mark)


if __name__ == "__main__":
    r = SentenceRules()
    examples = [
        r.noun_phrase("liv", determiner="the"),
        r.noun_phrase("chen", determiner="the"),
        r.noun_phrase("zanmi", determiner="the"),
        r.noun_phrase("machin", ["wouj"], determiner="the"),
        r.noun_phrase("kay", ["wouj", "ti", "bèl"], possessor="i", determiner="these"),
        r.noun_phrase("liv", number=2),
        r.possessive("liv", "i", definite=True),
        r.possessive_pronoun("i"),
        r.kreyol_sentence("i", "manje", tense="progressive"),
        r.kreyol_sentence("he", "vini", tense="past_progressive", negation="not"),
        r.kreyol_sentence("i", "ale", tense="future", negation="not"),
        r.kreyol_sentence("we", "ale", "lakay", tense="future"),
        r.kreyol_sentence("i", "wè", "li", negation="never"),
        r.kreyol_sentence("he", "rive", tense="past", negation="not_yet"),
        r.kreyol_sentence("you", "grangou", question="yes_no"),
        r.kreyol_sentence(None, "fè", "sa", tense="imperative", negation="not"),
        r.finish(r.predicate("li", "doktè")),
        r.finish(r.predicate("li", "malad", kind="adjective", tense="past")),
        r.wh_question("how", "you"),
        r.wh_question("who", verb="vini", tense="past", subject_question=True),
        r.finish(r.there_is(r.noun_phrase("dlo"), negation="not")),
        r.finish(r.relative("moun", "vini")),
        r.finish(r.connect(r.clause("i", "vle", "ale"), r.clause("i", "kapab", negation="not"), "but")),
    ]
    for line in examples:
        print(line)
    print()
    for rule_id, text in r.explain():
        print(f"{rule_id}: {text}")
