import re, lemminflect

def correct(sent, correction):
    return re.sub('<b>.*?</b>', correction, sent)

def get_corr_root(sent, correction, parser):
    left_length = len(parser(sent[:sent.find('<b>')]))
    corr_root_i = get_root(correction, parser).i + left_length
    corr_root_node = parser(correct(sent, correction))[corr_root_i]
    return corr_root_node

## Determining tenses:
def display_parse(string, parser):
    parse = parser(string)
    for token in parse:
        print(token.i, token.text, token.tag_, token.lemma_, token.pos_, token.head.i, token.dep_)

def get_root(string, parser):
    parse = parser(string)
    for token in parse:
        if token.dep_ == 'ROOT':
            return token
    return None

def get_voice(verb_node):
    for child in verb_node.children:
        if child.dep == 'auxpass':
            return 'passive', child
    return 'active', None

## Generating tenses:
def flatten(node):
    tokens = [node]
    for child in node.children:
        for child1 in flatten(child):
            tokens.append(child1)
    return tokens

def unite(token_nodes):
    token_nodes = sorted(token_nodes, key=lambda x: x.i)
    return ''.join([node.text_with_ws for node in token_nodes])

def textify(node):
    return unite(flatten(node))

def n_nodes(node):
    return len(flatten(node))

class WritableNode:
    def __init__(self, spacy_node, head=None):
        self.head = head
        self.i = spacy_node.i
        self.text = spacy_node.text
        self.whitespace = spacy_node.whitespace_
        self.text_with_ws = spacy_node.text + self.whitespace
        self.lemma = spacy_node.lemma_
        self.pos = spacy_node.pos_
        self.tag = spacy_node.tag_
        self.dep = spacy_node.dep_
        self.children = [WritableNode(child, self) for child in spacy_node.children]
        self._gather_children()
    
    def inflect(self, tag):
        self.tag = tag
        self.text = lemminflect.getInflection(self.lemma, tag)[0]
        self.text_with_ws = self.text + self.whitespace
    
    def insert_child(self, node):
        '''Insert child node with its right and left children'''
        self._right_toggle_children(node.i, n_nodes(node))
        node.head = self
        self.children.append(node)
        self._gather_children()
    
    def delete_child(self, child):
        self.children.remove(child)
        self._left_toggle_children(child.i, n_nodes(child))
        self._gather_children()
        
    def _gather_children(self):
        deps = [child.dep for child in self.children]
        self.deps = {dep: sorted([child for child in self.children if child.dep == dep],
                                  key=lambda x: x.i) for dep in deps}
    
    def _left_toggle_children(self, index, step=1):
        if self.i > index:
            self.i -= 1
        for child in self.children:
            child._left_toggle_children(index)
    
    def _right_toggle_children(self, index, step=1):
        if self.i >= index:
            self.i += step
        for child in self.children:
            child._right_toggle_children(index)
    
    def toggle_node_and_children(self, step):
        self.i += step
        for child in self.children:
            child.toggle_node_and_children(step)
    
    def leftmost_aux(self):
        auxes = [self]
        if 'aux' in self.deps:
            auxes += self.deps['aux']
        if 'auxpass' in self.deps:
            auxes += self.deps['auxpass']
        return sorted(auxes,key=lambda x: x.i)[0]
    
    def __repr__(self):
        return self.text
    
    __str__ = __repr__

def get_have():
    base_perfect_marker = object.__new__(WritableNode)
    for key, val in {'text':'have', 'text_with_ws': 'have ', 'lemma': 'have',
                     'pos':'VERB','tag':'VB', 'dep': 'aux', 'whitespace': ' ',
                     'deps': [], 'children': []}.items():
        base_perfect_marker.__setattr__(key, val)
    return base_perfect_marker

def get_be():
    base_progress_marker = object.__new__(WritableNode)
    for key, val in {'text':'be', 'text_with_ws': 'be ', 'lemma': 'be',
                     'pos':'VERB','tag':'VB', 'dep': 'auxpass', 'whitespace': ' ',
                     'deps':[], 'children': []}.items():
        base_progress_marker.__setattr__(key, val)
    return base_progress_marker

def get_will():
    will = object.__new__(WritableNode)
    for key, val in {'text':'will', 'text_with_ws': 'will ', 'lemma': 'will',
                     'pos':'VERB','tag':'MD', 'dep': 'aux', 'whitespace': ' ',
                     'deps':[], 'children': []}.items():
        will.__setattr__(key, val)
    return will

def get_would():
    would = object.__new__(WritableNode)
    for key, val in {'text':'would', 'text_with_ws': 'would ', 'lemma': 'would',
                     'pos':'VERB','tag':'MD', 'dep': 'aux', 'whitespace': ' ',
                     'deps': [], 'children': []}.items():
        would.__setattr__(key, val)
    return would

def get_do():
    do = object.__new__(WritableNode)
    for key, val in {'text':'do', 'text_with_ws': 'do ', 'lemma': 'do',
                     'pos':'VERB','tag':'VB', 'dep': 'aux', 'whitespace': ' ',
                     'deps': [], 'children': []}.items():
        do.__setattr__(key, val)
    return do

def get_did():
    did = object.__new__(WritableNode)
    for key, val in {'text':'did', 'text_with_ws': 'did ', 'lemma': 'do',
                     'pos':'VERB','tag':'VBD', 'dep': 'aux', 'whitespace': ' ',
                     'deps': [], 'children': []}.items():
        did.__setattr__(key, val)
    return did

def get_not():
    neg = object.__new__(WritableNode)
    for key, val in {'text':'not', 'text_with_ws': 'not ', 'lemma': 'not',
                     'pos':'ADV','tag':'RB', 'dep': 'neg', 'whitespace': ' ',
                     'deps': [], 'children': []}.items():
        neg.__setattr__(key, val)
    return neg

def passify(verb_node):
    ''' Accept verb node with base TAME
    Return veb node in passive voice '''
    passifier = get_be()
    passifier.i = verb_node.i
    verb_node.insert_child(passifier)
    verb_node.inflect('VBN')
    return verb_node

def progressify(verb_node):
    leftmost = verb_node.leftmost_aux()
    leftmost.inflect('VBG')
    progress_maker = get_be()
    progress_maker.i = leftmost.i
    verb_node.insert_child(progress_maker)
    return verb_node

def perfectify(verb_node):
    leftmost = verb_node.leftmost_aux()
    leftmost.inflect('VBN')
    have = get_have()
    have.i = leftmost.i
    verb_node.insert_child(have)
    return verb_node

def assign_tense(verb_node, tense='Present'):
    leftmost = verb_node.leftmost_aux()
    if tense == 'Past':
        leftmost.inflect('VBD')
    elif tense == 'FutureI':
        will = get_will()
        will.i = leftmost.i
        verb_node.insert_child(will)
    elif tense == 'FutureII':
        would = get_would()
        would.i = leftmost.i
        verb_node.insert_child(would)
    return verb_node

def negate(verb_node):
    leftmost = verb_node.leftmost_aux()
    if leftmost.dep == 'aux' or leftmost.lemma == 'be':
        neg = get_not()
        neg.i = leftmost.i+1
        verb_node.insert_child(neg)
    else:
        if leftmost.tag == 'VBD':
            did = get_did()
            did.i = leftmost.i
            verb_node.insert_child(did)
            neg = get_not()
            neg.i = leftmost.i
            verb_node.insert_child(neg)
            verb_node.inflect('VB')
        elif leftmost.tag == 'VB':
            do = get_do()
            do.i = leftmost.i
            verb_node.insert_child(do)
            neg = get_not()
            neg.i = leftmost.i
            verb_node.insert_child(neg)
    return verb_node

def assign_persn_nmb(verb_node, persn_nmb='3SG'):
    leftmost = verb_node.leftmost_aux()
    if leftmost.lemma == 'be':
        if leftmost.tag == 'VBD':
            if persn_nmb in ('1SG','3SG'):
                leftmost.text = 'was'
            elif persn_nmb in ('1PL', '2SG','2PL','3PL'):
                leftmost.text = 'were'
        elif leftmost.tag in ('VB','VBP','VBZ'):
            if persn_nmb == '1SG':
                leftmost.text = 'am'
                leftmost.tag = 'VBP'
            elif persn_nmb == '3SG':
                leftmost.text = 'is'
                leftmost.tag = 'VBZ'
            else:
                leftmost.text = 'are'
                leftmost.tag = 'VBP'
    elif leftmost.tag in ('VB', 'VBP') and persn_nmb=='3SG':
        leftmost.inflect('VBZ')
    leftmost.text_with_ws = leftmost.text + leftmost.whitespace
    return verb_node

def is_neg(verb_node):
    if 'neg' in verb_node.deps:
        if len(verb_node.deps['neg']) % 2 == 1:
            return True
    return False

def strip_TAME(verb_node):
    ## creating copy of a list of node pointers
    children = [child for child in verb_node.children if child.dep in ('auxpass', 'aux', 'neg')]
    ## deleting TAME children by pointers to them:
    for child in children:
        verb_node.delete_child(child)
    verb_node.inflect('VB')
    return verb_node

def toggle_mid_aux(verb_node):
    #print(textify(verb_node))
    if 'neg' in verb_node.deps:
        leftmost_aux = verb_node.deps['neg'][0]
    else:
        leftmost_aux = verb_node.leftmost_aux()
    if leftmost_aux.dep in ('aux', 'auxpass','neg'):
        if 'advmod' in verb_node.deps:
            adv_children = [adv for adv in verb_node.deps['advmod']]
            for adv in adv_children[::-1]:
                ## checking adverb phrase precedes leftmost aux:
                if adv.i < leftmost_aux.i:
                    ## checking there is no intervening immediate children:
                    interveners = [child for child in verb_node.children if child.i in range (adv.i+1, 
                                   leftmost_aux.i) and child.dep not in ('aux','auxpass')]
                    if not interveners:
                        verb_node.delete_child(adv)
                        delta = leftmost_aux.i + 1 - adv.i
                        adv.toggle_node_and_children(delta)
                        verb_node.insert_child(adv)
    return verb_node

def change_verb_form(string, parser, tense, perfect, progressive, neg=None, voice=None, persn_nmb = '3SG'):
    verb_node = get_root(string, parser)
    verb_node = WritableNode(verb_node)
    if not voice:
        voice, voice_marker = get_voice(verb_node)
    if neg == None:
        neg = is_neg(verb_node)
    verb_node = strip_TAME(verb_node)
    #print(textify(verb_node))
    if voice == 'passive':
        verb_node = passify(verb_node)
    #print(textify(verb_node))
    if progressive:
        verb_node = progressify(verb_node)
    #print(textify(verb_node))
    if perfect:
        verb_node = perfectify(verb_node)
    #print(textify(verb_node))
    if tense in ('Past', 'FutureI', 'FutureII'):
        verb_node = assign_tense(verb_node, tense)
    #print(textify(verb_node))
    #print(textify(verb_node))
    if neg:
        verb_node = negate(verb_node)
    verb_node = toggle_mid_aux(verb_node)
    #print(textify(verb_node))
    verb_node = assign_persn_nmb(verb_node, persn_nmb)
    #print(textify(verb_node))
    return verb_node

def test_change_verb_form(text, *args, **kwargs):
    x = change_verb_form(text, *args, **kwargs)
    print(textify(x))

## Determining tenses:

def is_future(verb_node):
    for child in verb_node.children:
        if child.dep == 'aux':
            if child.lemma == 'will':
                return 'Future I'
            elif child.lemma == 'would' or child.lemma == 'should':
                return 'Future II'
    return ''

def is_past(verb_node):
    if verb_node.leftmost_aux().tag in ('VBD','VBN'):
        return 'Past'
    return 'Present'

def is_perfect(verb_node):
    for child in verb_node.children:
        if child.dep == 'aux':
            if child.lemma == 'have':
                return 'Perfect', child
    return 'Simple', None

def is_progressive(verb_node, voice, voice_marker):
    if voice == 'passive':
        if voice_marker.tag == 'VBG':
            return 'continuous'
    else:
        if verb_node.tag == 'VBG':
            return 'continuous'
    
    return ''

def determine_tense(string, parser):
    verb_node = get_root(string, parser)
    if verb_node:
        verb_node = WritableNode(verb_node)
        voice, voice_marker = get_voice(verb_node)
        future = is_future(verb_node)
        perfect, perfect_marker = is_perfect(verb_node)
        progressive = is_progressive(verb_node, voice, voice_marker)
        if future:
            past = ''
            tense = future
        else:
            past = is_past(verb_node)
            tense = past
        outp = ' '.join([tense, perfect, progressive]).strip()
        outp = re.sub('\s+', ' ', outp)
        return outp, voice
    return '', ''

def get_subject(verb_node):
    nsubj = None

    if 'nsubj' in verb_node.deps:
        nsubj = verb_node.deps['nsubj'][0]
    elif 'nsubjpass' in verb_node.deps:
        nsubj = verb_node.deps['nsubjpass'][0]
    elif 'attr' in verb_node.deps:
        nsubj = verb_node.deps['attr'][0]
    elif verb_node.dep == 'conj' and verb_node.head:
        return get_subject(WritableNode(verb_node.head))

    return nsubj


def determine_persn_nmb(verb_node):
    persn_nmb = ''
    leftmost = verb_node.leftmost_aux()
    if leftmost.tag == 'VBZ':
        persn_nmb = '3SG'
    elif leftmost.text in ('are','were'):
        persn_nmb = '3PL'
    elif leftmost.text == 'am':
        persn_nmb = '1SG'
    elif leftmost.tag in ('VBN','VBD'):
        nsubj = get_subject(verb_node)
        
        if nsubj:
            if nsubj.tag not in ('NN','NNP','NNPS','NNS','PRP'):
                if verb_node.dep == 'relcl':
                    nsubj = WritableNode(verb_node.head)
            if nsubj.tag in ('NN', 'NNP'):
                persn_nmb = '3SG'
            elif nsubj.tag in ('NNS','NNPS'):
                persn_nmb = '3PL'
            elif nsubj.tag == 'PRP':
                if nsubj.text.lower() in ('he','she','it'):
                    persn_nmb = '3SG'
                elif nsubj.text.lower() == 'they':
                    persn_nmb = '3PL'
                elif nsubj.text.lower() == 'you':
                    persn_nmb = '2SG'
                elif nsubj.text.lower() == 'i':
                    persn_nmb = '1SG'
                elif nsubj.text.lower() == 'we':
                    persn_nmb ='1PL'
        elif 'csubj' or 'csubjpass' in verb_node.deps:
            persn_nmb = '3SG'
            if 'csubj' in verb_node.deps:
                nsubj = verb_node.deps['csubj'][0]
            if 'csubjpass' in verb_node.deps:
                nsubj = verb_node.deps['csubjpass'][0]
        
        if nsubj and persn_nmb:
            if 'conj' in nsubj.deps:
                persn_nmb = persn_nmb[0] + 'PL'

    return persn_nmb