"""Auto-tag the glosses in wordlist.csv with a word class.

    manje -> eat, food, meal   becomes   manje -> eat (v), food (n), meal (n)

Tags: n, v, v.stative, adj, adv, aux, prep, pron, det, conj, num, intj
A trailing '?' (e.g. "(n?)") marks a low-confidence guess that should be checked by hand.

Usage:
    python tag_wordlist.py                       # wordlist.csv -> wordlist_tagged.csv
    python tag_wordlist.py -i in.csv -o out.csv
    python tag_wordlist.py --review              # also print every low-confidence line
"""
import argparse
import re
from collections import Counter


def words(text):
    return set(text.split())


# ---- English closed classes ------------------------------------------------

PRONOUNS = words("""i me my mine myself you your yours yourself yourselves he him his himself
    she her hers herself it its itself we us our ours ourselves they them their theirs themselves
    someone somebody something anyone anybody anything everyone everybody everything nobody
    nothing one oneself who whom whose what which whoever whatever this that these those""")
DETERMINERS = words("""the a an each every some any no all both either neither several many
    much few little more most other another such enough""")
PREPOSITIONS = words("""in on at to from of with without by for about above below under over
    behind before after between among through into onto upon toward towards against during
    until till since near beside besides around across along inside outside within beyond
    despite except like unlike via per off up down out""")
CONJUNCTIONS = words("""and or but nor so yet because although though if unless while whereas
    when whenever where wherever that than whether as once""")
INTERJECTIONS = words("""oh ah hey hi hello bye goodbye alas wow ouch ugh hurray hooray amen
    hallelujah yes no okay ok please thanks psst shh oops bravo hush""")
NUMBERS = words("""zero one two three four five six seven eight nine ten eleven twelve thirteen
    fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy
    eighty ninety hundred thousand million billion first second third fourth fifth sixth seventh
    eighth ninth tenth half dozen""")
ADVERBS = words("""here there now then today tomorrow yesterday tonight always never often
    sometimes seldom rarely usually again already still yet soon later early late very too quite
    almost also only even just well together alone away back ahead abroad anyway maybe perhaps
    not instead indeed else ever forever meanwhile otherwise somewhere anywhere everywhere
    nowhere nearby once twice rather fast hard straight upstairs downstairs home how""")

# ---- English open classes (common words) ----------------------------------

VERBS = words("""abandon abuse accept accompany accuse ache achieve add admire admit adopt advise
    afford agree aim allow amuse announce annoy answer apologize appear applaud apply approach
    approve argue arrange arrest arrive ask assist attach attack attend avoid awake bake bang
    baptize bark bathe be bear beat become beg begin behave believe belong bend bet bind bite
    bleed bless blind blink blow boil borrow bother bounce bow break breathe breed bring broadcast
    brush build burn burst bury buy calculate call calm care carry carve catch cause celebrate
    change charge chase chat cheat check chew choke choose chop clap clean clear climb cling close
    collect comb come comfort command commit compare compete complain complete concern confess
    confuse connect consider consist contain continue convince cook copy correct cost cough count
    cover crawl create creep criticize cross crush cry cure curse cut damage dance dare deal
    decay deceive decide declare decorate defeat defend delay deliver demand deny depend descend
    describe deserve desire destroy develop die dig dine disagree disappear discover dislike
    dissolve dive divide do doubt drag drain draw dream dress drink drip drive drop drown dry dump
    dwell earn eat educate embarrass employ empty encourage end enjoy enter entertain escape
    examine excite excuse exercise exist expand expect explain explode extend fade fail faint
    fall fasten fear feed feel fetch fight fill find finish fit fix flap flash flee float flood
    flow fly fold follow forbid force forget forgive found freeze frighten fry gain gather get
    give glance glow go grab grant grasp grease greet grieve grind grip groan grow growl guard
    guess guide hammer hand handle hang happen harm hate have heal hear heat help hesitate hide
    hit hold hop hope hug hum hunt hurry hurt identify ignore imagine impress improve include
    increase inform inhabit injure insist inspire instruct insult intend interest interfere
    interrupt introduce invent invite irrigate itch join joke judge jump keep kick kill kiss
    kneel knit knock know land last laugh lay lead lean leap learn leave lend let lick lie lift
    light like limp listen live load lock look loosen lose love lower lunch make manage march
    marry matter measure meet melt mend milk miss mix moan mourn move mow multiply murder need
    nod notice obey obtain occur offend offer open order owe own pack paint park part pass pause
    pay peel perform permit persuade pick pinch plant play plead please plow plug point poke
    polish pour practice praise pray preach prefer prepare present preserve press pretend
    prevent print produce promise protect prove provide pull pump punch punish push put quarrel
    question quit race rain raise reach read realize receive recognize recommend record reduce
    refuse regret reign reject rejoice relax release rely remain remember remind remove rent
    repair repeat replace reply report request rescue resemble rest return reveal ride ring rinse
    rip rise roar rob rock roll rot rub ruin rule run rush sail satisfy save saw say scare scold
    scrape scratch scream screw search see seek seem sell send separate serve set settle sew
    shake share shave shelter shine shiver shock shoot shout show shrink shut sigh sign sing sink
    sip sit skip slap sleep slide slip smash smell smile smoke snatch sneeze sniff snore soak
    sob solve sow speak spell spend spill spin spit split spoil spray spread sprinkle squeeze
    stab stand stare start starve stay steal step stick sting stink stir stitch stop store
    strangle stretch strike strip struggle study stuff stumble subtract succeed suck suffer
    suggest supply support suppose surprise surround survive suspect swallow swear sweat sweep
    swell swim swing take talk tame taste teach tear tease tell tempt tend terrify test thank
    think threaten throw tickle tie tire touch tow trade train translate trap travel tremble
    trick trip trot trouble trust try tug turn twist understand undress unite untie urge use
    vanish visit vomit vote wait wake walk wander want warn wash waste watch water wave wear
    weave weep weigh welcome whip whisper whistle win wink wipe wish worry wound wrap wrestle
    write yawn yell""")

STATIVE_VERBS = words("""know love like want have need seem hate believe understand own prefer
    wish resemble owe belong deserve fear doubt mean contain consist depend matter possess
    dislike envy adore desire suppose realize recognize remember forget appear""")

ADJECTIVES = words("""able absent afraid alive angry anxious ashamed asleep awake awful bad
    bald bare beautiful best better big bitter black blind blond blue blunt bold bored boring
    brave brief bright brilliant broad broken brown busy calm careful cheap clean clear clever
    close cold comfortable common complete cool correct crazy crooked cruel curious curly cute
    damp dangerous dark dead deaf dear deep different difficult dirty dizzy dry dull dumb eager
    early easy elegant empty enormous entire equal evil exact excellent expensive extra faint
    fair fake false familiar famous fancy far fast fat fierce fine firm flat foolish foreign
    fortunate free fresh friendly full funny gentle giant glad good gorgeous grand gray great
    greedy green grey guilty handsome happy hard harsh healthy heavy high hollow holy honest hot
    huge humble hungry ill important innocent intelligent jealous kind large last late lazy
    lean left light little lively lone lonely long loose loud lovely low loyal lucky mad main
    male female married mean messy mild modern moist naked narrow nasty natural naughty near
    neat necessary nervous new nice noble noisy normal obvious odd old open orange ordinary
    pale perfect plain pleased plump polite poor popular possible pregnant pretty private
    proud pure purple quick quiet rapid rare raw ready real red rich right rotten rough round
    rude sad safe salty same scared secret selfish serious severe shallow sharp short shy sick
    silent silly similar simple single skinny slim slow small smart smooth soft sore sorry sour
    square stiff still strange strict strong stupid sudden sure sweet swift tall tame tender
    terrible thick thin thirsty tidy tight tiny tired tough true ugly unhappy upset useful vast
    violent warm weak wealthy weary wet white whole wicked wide wild wise worthless wrong yellow
    young""")

# Common both as noun and verb in English; resolved with the other glosses and Kreyòl cues
NOUN_VERB = words("""abuse answer attack bark bet bite blow boil brush call care charge chat
    check claim cook cost cough cover crack crash cry cure curse cut damage dance deal delay
    desire divorce doubt drink drive drop dump end escape exercise experience face fall fear
    fight fish fix flood fly fold force fry glance grease guard guess hammer hand harm hate
    heat help hit hold hope hug hunt itch joke judge jump kick kill kiss knock land laugh lead
    leap lie lift light limp load lock look love lunch march mark match milk mind miss mix
    murder name need nod order paint park pass pause pay pick pinch plant play plow plug point
    poke polish practice praise present press print promise pull pump punch push question race
    rain reach record reign rent repair reply report request rescue rest return ride ring rip
    rise roar rock roll rub ruin rule run rush sail saw scare scratch scream screw search sew
    shake share shave shelter shock shout show sigh sign sip skip slap sleep slide slip smell
    smile smoke sneeze sniff snore sob spell spill spin spit split spray spread squeeze stab
    stand stare start step stick sting stink stir stitch stop store strike strip struggle study
    stuff stumble supply support surprise swallow sweat swim swing talk taste tear test thank
    throw tie tire touch tow trade train trap travel trick trip trot trouble trust try tug turn
    twist use visit vomit vote wait walk wash waste watch water wave weep welcome whip whisper
    whistle wink wish work worry wound wrap yawn yell""")

NOUN_SUFFIXES = ("tion", "sion", "ment", "ness", "ity", "ism", "ist", "ship", "hood", "ance",
                 "ence", "ery", "ary", "ure", "dom", "ician", "logy", "graphy", "eer", "ette",
                 "ster", "itis")
AGENT_SUFFIXES = ("er", "or", "ian", "ant", "ent")   # person nouns (often also adjectives)
ADJ_SUFFIXES = ("ous", "ful", "less", "ive", "able", "ible", "ical", "ish", "ic", "ary",
                "ial", "al", "ent", "ant", "ky", "ty", "dy", "sy", "py", "ny")
VERB_SUFFIXES = ("ize", "ise", "ify", "en")
NOT_ADVERB_LY = words("""ugly holy lonely lovely friendly silly early daily only jolly ally fly
    family belly lily rally supply apply reply rely bully july italy comply assembly anomaly
    homily melancholy monopoly butterfly dragonfly firefly jelly hilly smelly curly chilly
    elderly likely costly deadly lively orderly ghostly cowardly kindly""")

MODALS = words("will shall can could would should must may might")
PARTICLES = PREPOSITIONS | ADVERBS | PRONOUNS | DETERMINERS | words("how")
OPEN = ("n", "v", "v.stative", "adj")


def base(tag):
    return tag.split(".")[0]


def gloss_tag(gloss):
    """Return (candidate tags in preference order, confident) using only the English gloss."""
    g = re.sub(r"^to ", "", gloss.casefold().strip())
    parts = g.split()
    if not parts:
        return ["n"], False

    if len(parts) > 1:
        first, rest, last = parts[0], parts[1:], parts[-1]
        if first == "be":
            return (["v.stative"] if rest[0] in ADJECTIVES else ["v"]), True
        if first in PREPOSITIONS:
            return (["prep"] if last in PREPOSITIONS else ["adv"]), True
        if len(parts) == 2 and rest[0] in words("up down out off away over back"):
            return ["v"], True                                    # phrasal verb: pile up
        if first in VERBS and first not in ADJECTIVES:
            verb = "v.stative" if first in STATIVE_VERBS and first != "have" else "v"
            phrasal = (len(parts) > 2 or rest[0] in PARTICLES or rest[0] in ADJECTIVES
                       or rest[0].endswith("ed"))
            return ([verb] if phrasal else ["n", verb]), True     # 'love affair' is a noun
        if (first in ADJECTIVES or first in ADVERBS) and last.endswith(("ing", "ed")):
            return ["adj"], True                                  # good looking, well dressed
        if first in ("a", "an", "the") or first in ADJECTIVES or first in NUMBERS:
            return ["n"], True
        if last.endswith("ly") and last not in NOT_ADVERB_LY:
            return ["adv"], True
        if first in CONJUNCTIONS or g in ("as if", "even though", "so that"):
            return ["conj"], True
        if first.endswith("ing"):
            return ["v"], False
        if last.endswith(NOUN_SUFFIXES + AGENT_SUFFIXES):
            return ["n"], True
        return ["n"], False

    w = parts[0]
    cands = []
    if w in MODALS:
        cands.append("aux")
    for wordset, tag in ((PRONOUNS, "pron"), (NUMBERS, "num"), (INTERJECTIONS, "intj"),
                         (PREPOSITIONS, "prep"), (CONJUNCTIONS, "conj"), (DETERMINERS, "det"),
                         (ADVERBS, "adv")):
        if w in wordset:
            cands.append(tag)
    verb = "v.stative" if w in STATIVE_VERBS else "v"
    if w in NOUN_VERB:
        cands += ["n", verb]
    elif w in VERBS or w in STATIVE_VERBS:
        cands.append(verb)
    if w in ADJECTIVES:
        cands.append("adj")
    if cands:
        return cands, True

    if w.endswith("ly") and w not in NOT_ADVERB_LY:
        return ["adv"], True
    if w.endswith(NOUN_SUFFIXES):
        return ["n"], True
    if w.endswith(VERB_SUFFIXES[:3]):
        return ["v"], True
    if w.endswith("ed") and len(w) > 4:
        return ["adj", "v"], False
    if w.endswith("ing") and len(w) > 5:
        return ["n", "v"], False
    if w.endswith(AGENT_SUFFIXES) and len(w) > 4:
        return ["n", "adj"], False
    if w.endswith(ADJ_SUFFIXES) and len(w) > 4:
        return ["adj"], False
    return ["n"], None            # unknown word: noun by default (None = decide from context)


def kreyol_cue(word, all_kreyol):
    """Guess a class from the shape of the Kreyòl word. Returns a tag or None."""
    w = word.casefold()
    if w.startswith("la") and w[2:] in all_kreyol:
        return "n"                    # agglutinated article: labatwa, lakay
    if w.endswith(("syon", "man", "aj", "ite", "ri")):
        return "n"
    if w.endswith(("nen", "ye", "e", "en")):
        return "v"
    return None


def tag_entry(kreyol, glosses, all_kreyol):
    """Return [(gloss, tag, confident)] for one dictionary line.

    Ambiguous glosses take the class most of the entry's unambiguous glosses agree on,
    then the class suggested by the Kreyòl word's shape.
    """
    raw = [(g, *gloss_tag(g)) for g in glosses]
    votes = Counter(base(c[0]) for _, c, ok in raw if ok and len(c) == 1 and c[0] in OPEN)
    majority = votes.most_common(1)[0][0] if votes else None
    cue = kreyol_cue(kreyol, all_kreyol)

    result = []
    for gloss, cands, confident in raw:
        tag = cands[0]
        if len(cands) > 1:
            by_majority = [c for c in cands if base(c) == majority]
            by_cue = [c for c in cands if base(c) == cue]
            if by_majority:
                tag, confident = by_majority[0], True
            elif by_cue:
                tag, confident = by_cue[0], True
            elif not any(c in OPEN for c in cands[1:]):
                confident = True      # closed-class alternatives only: keep the first
            else:
                confident = False
        elif confident is None:
            # unknown single word: usually a noun (common verbs/adjectives are in the lists).
            # A -nen ending is a strong verb sign; any other conflict just flags it for review.
            if kreyol.casefold().endswith("nen"):
                tag, confident = "v", majority == "v"
            else:
                confident = cue != "v" and majority in (None, "n")
        elif not confident and (base(tag) == cue or base(tag) == majority):
            confident = True
        result.append((gloss, tag, confident))
    return result


def tag_lines(lines):
    """Tag dictionary lines. Returns (tagged lines, tag counts, low-confidence lines).
    Comment lines and anything without ' -> ' pass through unchanged."""
    all_kreyol = {line.split(" -> ")[0].strip().casefold() for line in lines if " -> " in line}
    tag_counts, unsure_lines, out = Counter(), [], []

    for line in lines:
        parts = line.split(" -> ")
        if len(parts) != 2:
            out.append(line)
            continue
        kreyol = parts[0].strip()
        glosses = [g.strip() for g in parts[1].split(",") if g.strip()]
        tagged = tag_entry(kreyol, glosses, all_kreyol)
        for _, tag, confident in tagged:
            tag_counts[tag + ("" if confident else "?")] += 1
        text = ", ".join(f"{g} ({t}{'' if ok else '?'})" for g, t, ok in tagged)
        new_line = f"{kreyol} -> {text}"
        if not all(ok for _, _, ok in tagged):
            unsure_lines.append(new_line)
        out.append(new_line)
    return out, tag_counts, unsure_lines


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", default="wordlist.csv")
    parser.add_argument("-o", "--output", default="wordlist_tagged.csv")
    parser.add_argument("--review", action="store_true", help="print the low-confidence lines")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]
    out, tag_counts, unsure_lines = tag_lines(lines)

    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")

    total = sum(tag_counts.values())
    unsure = sum(c for t, c in tag_counts.items() if t.endswith("?"))
    print(f"wrote {args.output}: {total} glosses, {unsure} low-confidence ({unsure / total:.0%})")
    for tag, count in sorted(tag_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {tag:<11}{count}")
    if args.review:
        print("\nlow-confidence lines:")
        for line in unsure_lines:
            print("  " + line)


if __name__ == "__main__":
    main()
