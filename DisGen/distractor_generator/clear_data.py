import re
from . import Tenses

def contains_pos(string, pos, parser):
    if string and type(string) == str:
        parse = parser(string)
        pos_string = [token.pos_ for token in parse]
        if set(pos_string) & set(pos):
            return True
    return False

def find_error(string):
    return re.search('<b>(.*?)</b>',string).group(1)

def get_lemmas(row, parser):
    wrong_lemma = Tenses.get_root(row['Wrong answer'], parser).lemma_
    right_lemma = Tenses.get_root(row['Right answer'], parser).lemma_
    return wrong_lemma, right_lemma

def correct(sent, correction):
    return re.sub('<b>.*?</b>', correction, sent)

def is_corr_root_aux(sent, correction, parser):
    corr_root_node = Tenses.get_corr_root(sent, correction, parser)
    if corr_root_node.dep_ in ('aux', 'auxpass'):
        return True
    return False

def persn_nmb(sent, correction, parser):
    root = Tenses.get_root(correction, parser)
    if root.tag_ == 'VBZ':
        return '3SG'
    elif root.text in ('are','were'):
        return '3PL'
    elif root.text == 'am':
        return '1SG'
    else:
        corr_root = Tenses.get_corr_root(sent, correction, parser)
        corr_root = Tenses.WritableNode(corr_root, head=corr_root.head)
        #print(sent, correction, corr_root, type(corr_root))
        return Tenses.determine_persn_nmb(corr_root)

def remove_err_span(string):
    match = re.search('<b>.*?</b>', string)
    output = (string[:match.start()], string[match.end():])
    return output

def is_one_word(string, parser):
    tokens = parser(string)
    if len(tokens) == 1:
        word = tokens[0]
        return True, word.lemma_, word.pos_, word.tag_
    return False, '', '', ''

def is_prep(string, parser):
    tokens = parser(string)
    if len(tokens) == 1:
        word = tokens[0]
        if word.pos_ == 'ADP':
            return True
    return False
