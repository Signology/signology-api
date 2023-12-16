import os
import re
from application import app
from collections import Counter
from nlp_id.postag import PosTag
postagger = PosTag() 
# build language model
def words(text): return re.findall(r'\w+', text.lower())
path_corpus = os.path.join(app.config["DATASET_AUTOCORRECT"])
WORDS = Counter(words(open(path_corpus).read()))


def P(word, N=sum(WORDS.values())): 
    "Probability of `word`."
    return WORDS[word] / N

    # selection mechanism
def correction(word): 
    "Most probable spelling correction for word."
    return max(candidates(word), key=P)

# candidate model
def candidates(word): 
    "Generate possible spelling corrections for word."
    return (known([word]) or known(edits1(word)) or known(edits2(word)) or [word])

# error model
def known(words): 
    "The subset of `words` that appear in the dictionary of WORDS."
    return set(w for w in words if w in WORDS)

def edits1(word):
    "All edits that are one edit away from `word`."
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)

def edits2(word): 
    "All edits that are two edits away from `word`."
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))


def autocorrect_text(sentence):
    words = sentence.split()
    corrected_words =[]
    pos_word = postagger.get_pos_tag(sentence)
    for i, word in enumerate(words):
        if pos_word[i][1] != "NNP":
            corrected_words.append(correction(word))
        else:
            corrected_words.append(word)
            
    result_corrected_words = " ".join(corrected_words)
    
    return result_corrected_words
    

