from . import Tenses
from random import choice

def determine_polarity(string, parser):
    right_root = Tenses.get_root(string, parser)
    right_root = Tenses.WritableNode(right_root)
    polarity = Tenses.is_neg(right_root)
    return polarity

def binary_encode_tense(tense):
    s = ''
    
    if 'Future II' in tense:
        s += '11'
    elif 'Future I' in tense:
        s += '01'
    elif 'Past' in tense:
        s += '10'
    elif 'Present' in tense:
        s += '00'
    
    if 'Simple' in tense:
        s += '0'
    elif 'Perfect' in tense:
        s += '1'
    
    if 'continuous' in tense:
        s += '1'
    else:
        s += '0'
    
    return s

def decode_binary_tense(seq):
    if seq[:2] == '00':
        tense = 'Present'
    elif seq[:2] == '01':
        tense = 'FutureI'
    elif seq[:2] == '10':
        tense = 'Past'
    elif seq[:2] == '11':
        tense = 'FutureII'
    else:
        raise Exception(f"Incorrect tense format - {tense}")
    
    progressive, perfect = False, False
    
    if seq[2] == '1':
        perfect = True
    
    if seq[3] == '1':
        progressive = True
    
    return {'tense': tense,
            'perfect': perfect,
            'progressive': progressive}

def all_1bit_inversions(seq):
    seqs = []
    for symb_id, symb in enumerate(seq):
        if symb == '1':
            new_seq = seq[:symb_id]+'0'+seq[symb_id+1:]
        else:
            new_seq = seq[:symb_id]+'1'+seq[symb_id+1:]
        seqs.append(new_seq)
    return seqs

def mid_inversions(seq1, seq2):
    changes = []
    for symb_id, (symb1, symb2) in enumerate(zip(seq1, seq2)):
        if symb2 != symb1:
            changes.append(symb_id)
    
    seqs = []
    
    
    for diff_symb_id in changes:
        if seq1[diff_symb_id] == '1':
            seqs.append(seq1[:diff_symb_id]+'0'+seq1[diff_symb_id+1:])
        else:
            seqs.append(seq1[:diff_symb_id]+'1'+seq1[diff_symb_id+1:])
    
    # if len(seqs) > 2:
    #     print(seq1, seq2, changes)
    
    return seqs

def reverse_symb(seq, change_index):
    if seq[change_index] == '0':
        return seq[:change_index]+'1'+seq[change_index+1:]
    elif seq[change_index] == '1':
        return seq[:change_index]+'0'+seq[change_index+1:]

def diff_1_inversions(seq1, seq2):
    diff_index = 0
    for i, (symb1, symb2) in enumerate(zip(seq1, seq2)):
        if symb1 != symb2:
            diff_index = i

    ## don't take future forms as distractors for non-future forms:
    change_points = [i for i in range(3) if i!=diff_index and i!=1]

    change_index = choice(change_points)

    out_seq1 = reverse_symb(seq1, change_index)
    out_seq2 = reverse_symb(seq2, change_index)

    return (out_seq1, out_seq2)


def get_tense_distractors(example, estimator, parser):
    bin_right_tense = binary_encode_tense(example['Right tense'])
    bin_wrong_tense = binary_encode_tense(example['Wrong tense'])
    distance = estimator.distance(bin_right_tense, bin_wrong_tense)
    if distance == 1:
        # distractors = [i for i in all_1bit_inversions(bin_wrong_tense) if i!=bin_right_tense]
        distractors = diff_1_inversions(bin_right_tense, bin_wrong_tense)
        distractors = [decode_binary_tense(i) for i in distractors]
        distractors = [Tenses.change_verb_form(example['Right answer'],
                                               parser, distractor['tense'],
                                               distractor['perfect'],
                                               distractor['progressive'],
                                               example["Neg"],
                                               example["Voice"],
                                               example["Person/Number"]) for distractor in distractors]
        distractors = [Tenses.textify(d) for d in distractors]
        distractors.append(None)
        return distractors
    elif distance == 2:
        distractors = mid_inversions(bin_wrong_tense, bin_right_tense)
        distractors = [decode_binary_tense(i) for i in distractors]
        distractors = [Tenses.change_verb_form(example['Right answer'],
                                               parser, distractor['tense'],
                                               distractor['perfect'],
                                               distractor['progressive'],
                                               example["Neg"],
                                               example["Voice"],
                                               example["Person/Number"]) for distractor in distractors]
        distractors = [Tenses.textify(d) for d in distractors]
        distractors.append(None)
        return distractors
    else:
        return None, None, None