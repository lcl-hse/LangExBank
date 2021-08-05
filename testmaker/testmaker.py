import sys, codecs, re, os, shutil, traceback
from collections import defaultdict, OrderedDict
from datetime import datetime
import shutil
import random
import json, csv
import pprint
import difflib
import time
from . import realec_helper, wordforms, testmaker_utils
import io
import html
from .hierarchy import hierarchy

from tqdm import tqdm_notebook
   

"""Script that generates grammar exercises from REALEC data 
grammar tags:
	Punctuation
	Spelling
	Capitalisation
	Grammar
		Determiners
			Articles
				Art_choice
				Art_form
			Det_choice
			Det_form
		Quantifiers
			Quant_choice
			Quant_form
		Verbs
			Tense
				Tense_choice
					Seq_of_tenses
					Choice_in_cond
				Tense_form
					Neg_form
					Form_in_cond
			Voice
				Voice_choice
				Voice_form
			Modals
				Modals_choice
				Modals_form
			Verb_pattern
				Intransitive
				Transitive
					Reflexive_verb
					Presentation
				Ambitransitive
				Two_in_a_row
					Verb_Inf
						Verb_object_inf
						Verb_if
					Verb_Gerund
						Verb_prep_Gerund
							Verb_obj_prep_Gerund
					Verb_Inf_Gerund
						No_diff
						Diff
					Verb_Bare_Inf
						Verb_object_bare
						Restoration_alter
					Verb_part
						Get_part
					Complex_obj
					Verbal_idiom
				Prepositional_verb
					Trans_phrasal
					Trans_prep
					Double_object
					Double_prep_phrasal
				Dative
				Followed_by_a_clause
					that_clause
					if_whether_clause
					that_subj_clause
					it_conj_clause
			Participial_constr
			Infinitive_constr
			Gerund_phrase
			Verb_adj
			Verb_adv
		Nouns
			Countable_uncountable
			Prepositional_noun
			Possessive
			Noun_attribute
			Noun_inf
			Noun_number
				Collective
					Adj_as_collective
		Prepositions
		Conjunctions
			And_syn
			Contrast
			Concession
			Causation
		Adjectives
			Comparative_adj
			Superlative_adj
			Prepositional_adjective
			Adjective_inf
			Adjective_ger
		Adverbs
			Comparative_adv
			Superlative_adv
			Prepositional_adv
			Modifier
		Numerals
			Num_choice
			Num_form
		Pronouns
			Personal
			Reflexive
			Demonstrative
		Agreement_errors
			Animacy
			Number
			Person
		Word_order
			Standard
			Emphatic
			Cleft
			Interrogative
		Abs_comp_clause
			Exclamation
			Title_structure
			Note_structure
		Conditionals
			Cond_choice
			Cond_form
		Attributes
			Relative_clause
				Defining
				Non_defining
				Coordinate
			Attr_participial
		Lack_par_constr
		Negation
		Comparative_constr
			Numerical
		Confusion_of_structures
	Vocabulary
		Word_choice
			lex_item_choice
				Often_confused
			Choice_synonyms
			lex_part_choice
				Absence_comp_colloc
				Redundant
		Derivation
			Conversion
			Formational_affixes
				Suffix
				Prefix
			Category_confusion
			Compound_word
	Discourse
		Ref_device
			Lack_of_ref_device
			Dangling_ref
			Redundant_ref
			Choice_of_ref
		Coherence
			Incoherent_articles
			Incoherent_tenses
				Incoherent_in_cond
			Incoherent_pron
			Linking_device
				Incoherent_conj
				Incoherent_intro_unit
				Lack_of_connective
		Inappropriate_register
		Absence_comp_sent
		Redundant_comp
		Tautology
		Absence_explanation
"""

def create_folder_from_questions(questions, folder_name):
    pass

def get_fname_time():
    dt = datetime.now()
    str_date = str(dt.date()).replace('-', '_').strip()
    str_time = str(dt.time()).replace(':','_').replace('.', '').strip()
    return str_date+'_'+str_time

def sent_tokenize_function(s):
    sents = []
    sent = ''
    escaped = False
    capital = False
    prev_sym = ''
    for sym in s:
        sent += sym
        if sym == '<' and prev_sym == '<':
            escaped = True
        elif sym == '>' and prev_sym == '>':
            escaped = False
        elif sym in '?!.':
            if not (escaped or capital):
                sents.append(sent)
                sent = ''
            else:
                pass
        elif capital:
            capital = False
        elif sym.isupper():
            capital = True
        prev_sym = sym
    sents.append(sent)
    return sents

def split_arrows(s):
    try:
        correction, other = s[5].split('>>')
        s[5] = correction
        s.append(other)
    except:
        print(s)
        exit()
    return s

class Exercise:
    def __init__(self, path_to_realecdata = None, exercise_types = None, output_path = None,
     ann = None, text = None, error_types = [], bold = False, context = False, mode = 'folder',
      maintain_log = True, show_messages = True, use_ram=False,output_file_names = None,
      file_output = True, write_txt = False, keep_processed = True, hier_choice = False, moodle_output = True,
      make_two_variants = False, exclude_repeated = False, include_smaller_mistakes = False, file_prefix = os.getcwd()+os.sep,
      keep_all_exercises = False, use_tqdm=False, filter_query=None):

        """"
        :param error_types: list of str, can include values from
        'Tense_choice', 'Tense_form', 'Voice_choice', 'Voice_form', 'Number', e.g.
        :param exercise_types: list of str, any from: 'multiple_choice', 'word_form', 'short_answer', 'open_cloze'
        :param bold: bool, whether to write error region in bold text
        :param context: bool, whether to include contexts (one sentence before and
        one sentence after) for sentences in exercises
        :param show_messages: bool, whether to display messages in console while generating exercises
        :param write_txt: whether to include plain text representation of exercises in the output along
        with Moodle XML files or ByteIO objects
        :param use_ram: bool
        :param mode: str
        :param path_to_realecdata: str, path to directory with .txt and .ann files if mode == 'folder'
        alternatively path to an .ann file if mode == 'file'
        :param file_output: bool
        :param output_file_names: list of str
        """
        self.moodle_output = moodle_output
        self.file_prefix = file_prefix
        self.exercise_types = exercise_types
        self.error_type = error_types
        self.keep_processed = keep_processed
        # print(self.error_type)
        self.hier_choice = hier_choice
        if self.hier_choice:
            self.get_hierarchy = lambda x: hierarchy[x] if x in hierarchy else 0
            self.hier_sort = lambda x: sorted(x,key = self.get_hierarchy, reverse = True)
        self.make_two_variants = make_two_variants
        self.exclude_repeated = exclude_repeated
        # self.sent_tokenize_processed = lambda x: re.findall(r".*?\*\*[0-9]+\*\*.*?[\.?!]",x)
        self.sent_tokenize_processed = sent_tokenize_function
        # (([A-Z][^\[]*)?(\[[^\[]*\][^\[]*)*[\.\?!]) - регулярное выражение, которое лучше соответствует предложению, но тогда область ошибки
        # должна полностью обрамляться символами <> (знак > должен стоять после неправильного варианта, закрывая область ошибки) - 
        # добавить на будущее
        self.to_include = lambda x: True if (x["Error"] in self.error_type or self.error_type==[''] or not self.error_type) and (x["Relation"]!="Dependant_change") else False
        self.current_doc_errors = OrderedDict()
        self.bold = bold
        self.context = context
        self.write_txt = write_txt
        self.use_ram = use_ram
        self.mode = mode
        if self.mode in ('file','direct_input') and self.make_two_variants:
            ##пока делаем возможность использовать во втором варианте ошибки
            ##с меньшей областью, только если на вход поступает одно эссе:
            self.include_smaller_mistakes = include_smaller_mistakes
        else:
            self.include_smaller_mistakes = False
        self.file_output = file_output
        ##Note: maintain_log is forcibly set to False if file_output is False
        self.maintain_log = maintain_log
        self.show_messages = show_messages
        if self.use_ram:
            self.processed_texts = []
        else:
            self.path_new = self.file_prefix + 'processed_texts/'
        if self.mode == 'direct_input':
            self.ann = ann
            self.text = text
        else:
            self.path_old = path_to_realecdata
        if self.file_output:
            if not output_path:
                output_path = 'moodle_exercises'
            print(self.file_prefix, output_path)
            self.output_path = self.file_prefix + output_path
            os.makedirs(self.output_path, exist_ok = True)
            if output_file_names:
                self.output_file_names = output_file_names
            else:
                self.output_file_names = dict()
                for ex_type in self.exercise_types:
                    if self.make_two_variants:
                        ex_type1 = ex_type+'_variant1'
                        ex_type2 = ex_type+'_variant2'
                        self.output_file_names[ex_type1] = self.output_path+'/{}_{}'.format(''.join([str(i) for i in time.localtime()]),
                                                                                            ex_type1+'_context_'+str(self.context))
                        self.output_file_names[ex_type2] = self.output_path+'/{}_{}'.format(''.join([str(i) for i in time.localtime()]),
                                                                                            ex_type2+'_context_'+str(self.context))
                    else:
                        self.output_file_names[ex_type] = self.output_path+'/{}_{}'.format(''.join([str(i) for i in time.localtime()]),
                                                                                            ex_type+'_context_'+str(self.context))
        else:
            self.maintain_log = False
            self.output_objects = dict()
        if self.maintain_log:
            self.log = []
            self.fieldnames = ["ex_type","text","answers","to_skip","result"]
            self.log_name = '_'.join(self.exercise_types)+'_context='+str(self.context)+'_'+''.join([str(i) for i in time.localtime()])
        self.headword = ''
        self.write_func = {
            "short_answer": self.write_sh_answ_exercise, ##exerciese with selected error region
            "multiple_choice": self.write_multiple_ch, ##exercises with multiple answer selection
            "word_form": self.write_open_cloze, ##exercises where word is to be assigned the appropriate grammar
            "open_cloze": self.write_open_cloze ##exercises where you need to insert something in gap
        }
        if not self.use_ram:
            os.makedirs(self.file_prefix+'processed_texts', exist_ok=True)
        self.wf_dictionary = wordforms.wordforms  # {'headword':[words,words,words]}
        self.keep_all_exercises = keep_all_exercises
        self.tqdm = use_tqdm
        self.filter_query = filter_query
        print(f"Filter query - {self.filter_query}")

    def find_errors_indoc(self, line):
        """
        Find all T... marks and save in dictionary.
        Format: {"T1":{'Error':err, 'Index':(index1, index2), "Wrong":text_mistake}}
        """
        if re.search('^T', line) is not None and 'pos_' not in line:
            try:
                t, span, text_mistake = line.strip().split('\t')
                err, index1, index2 = span.split()
                if err!='note':
                    self.current_doc_errors[t] = {'Error':err, 'Index':(int(index1), int(index2)), "Wrong":text_mistake, "Relation":None}
            except:
                #print (''.join(traceback.format_exception(*sys.exc_info())))
                #print("Errors: Something wrong! No notes or a double span", line)
                pass

    def validate_answers(self, answer, error):
        # TO DO: multiple variants?
        if answer.upper() == answer:
            answer = answer.lower()
        answer = answer.strip(r'\'"')
        answer = re.sub(r' ?\(.*?\) ?','',answer)
        if '/' in answer:
            answer = answer.split('/')[0]
        if '\\' in answer:
            answer = answer.split('\\')[0]
        if ' OR ' in answer:
            answer = answer.split(' OR ')[0]
        if ' или ' in answer:
            answer = answer.split(' или ')[0]
        if answer.strip('? ') == '' or '???' in answer:
            return None
        ##если убирается запятая, следим, чтобы исправление начиналось с пробела,
        ##иначе дописываем его к исправлению:
        if error[0] in '.,:' and answer[0] not in ' .,:':
            answer = ' '+answer
        return answer

    def find_answers_indoc(self, line):
        if re.search('^#', line) is not None and 'lemma =' not in line:
            try:
                number, annotation, correction = line.strip().split('\t')
                t_error = annotation.split()[1]
                err = self.current_doc_errors.get(t_error)
                if err:
                    validated = self.validate_answers(correction,err.get('Wrong'))
                    if validated is not None:
                        self.current_doc_errors[annotation.split()[1]]['Right'] = validated
            except:
                #print (''.join(traceback.format_exception(*sys.exc_info())))
                #print("Answers: Something wrong! No Notes probably", line)
                pass

    def find_relations_indoc(self, line):
        if re.search('^R', line) is not None:
            try:
                number, relation = line.strip().split('\t')
                relation_type, *relation_args = relation.split()
                relation_args = list(map(lambda x: x.split(':')[1], relation_args))
                for arg in relation_args:
                    self.current_doc_errors[arg]["Relation"] = relation_type
            except:
                #print("Relations: Something wrong! No Notes or relation between non-error tags", line)
                pass
    
    def find_delete_seqs(self, line):
        if re.search('^A', line) is not None and 'Delete' in line:
            t = line.strip().split('\t')[1].split()[1]
            if self.current_doc_errors.get(t):
                self.current_doc_errors[t]['Delete'] = 'True'

    def make_data_ready_4exercise(self):
        """ Collect errors info """
        print('collecting errors info...')
        if self.mode == 'folder':
            # print(self.path_new)
            annpaths = []
            for root, dire, files in os.walk(self.path_old):
                for f in files:
                    if f.endswith('.ann') and os.path.exists(root+'/'+f+'.txt'):
                        annpath = root+'/'+f
                        annpaths.append(annpath)

            if self.tqdm:
                annpaths = tqdm_notebook(annpaths, total=len(annpaths))

            for i, annpath in enumerate(annpaths):
                if self.show_messages:
                    print(annpath)
                self.parse_ann_and_process_text(ann = annpath, processed_text_filename = str(i))
                    
        elif self.mode == 'file':
            self.parse_ann_and_process_text(ann = self.path_old)
        elif self.mode == 'direct_input':
            self.parse_ann_and_process_text()

    def parse_ann_and_process_text(self, ann=None, processed_text_filename = None):
        self.error_intersects = set()
        if self.mode!='direct_input':
            with open(ann, 'r', encoding='utf-8') as ann_file:
                annlines = ann_file.readlines()
            meta = testmaker_utils.load_meta(ann[:-4])
        else:
            annlines = self.ann.splitlines()
            meta = testmaker_utils.empty_meta()
        for method in (self.find_errors_indoc, self.find_answers_indoc, self.find_relations_indoc, self.find_delete_seqs):
            for line in annlines:
                method(line)
            
        new_errors = OrderedDict()
        for x in sorted(self.current_doc_errors.items(),key=lambda x: (x[1]['Index'][0],x[1]['Index'][1],int(x[0][1:]))):
            if 'Right' in x[1] or 'Delete' in x[1]:
                new_errors[x[0]] = x[1]
        self.current_doc_errors = new_errors
        
        unique_error_ind = []
        error_ind = [self.current_doc_errors[x]['Index'] for x in self.current_doc_errors]
        ##если области ошибки совпадают оставляем те,
        ##которые записаны первыми
        for ind in error_ind:
            if ind in unique_error_ind:
                self.error_intersects.add(ind)
            else:
                unique_error_ind.append(ind)                
        self.embedded,self.overlap1,self.overlap2 = self.find_embeddings(unique_error_ind)
        if self.use_ram:
            if self.mode == 'file' or self.mode == 'folder':
                self.add_to_processed_list(filename = ann[:ann.find('.ann')], meta=meta)
            elif self.mode == 'direct_input':
                self.add_to_processed_list(meta=meta)
        else:
            if self.mode == 'folder':
                self.make_one_file(ann[:ann.find('.ann')],processed_text_filename)
                testmaker_utils.save_meta(meta, os.path.join(self.path_new+processed_text_filename+'.json'))
            elif self.mode == 'direct_input':
                self.save_processed(self.text, output_filename=self.path_new+'processed')
                testmaker_utils.save_meta(meta, os.path.join(self.path_new+'processed'+'.json'))
            
        if not self.include_smaller_mistakes:
            self.current_doc_errors.clear()

    def find_embeddings(self,indices):
        ##сортируем исправления - сначала сортируем по возрастанию первого индекса,
        ##потом по убыванию второго индекса:
        indices.sort(key=lambda x: (x[0],-x[1]))
        embedded = []
        overlap1, overlap2 = [],[]
        self.embedding = defaultdict(list)
        for i in range(1,len(indices)):
            find_emb = [x for x in indices if (x[0] <= indices[i][0] and x[1] > indices[i][1]) or \
                                              (x[0] < indices[i][0] and x[1] >= indices[i][1])]
            if find_emb:
                ##в self.embedding для каждой ошибки с большей областью записываем текущую ошибку:
                for j in find_emb:
                    self.embedding[str(j)].append(indices[i])
                ##в self.embedded записываем те ошибки, для которых есть ошибки с большей областью:
                embedded.append(indices[i])
            else:
                overlaps = [x for x in indices if x[0] < indices[i][0] and (x[1] > indices[i][0] and
                                                                            x[1] < indices[i][1])]
                if overlaps:
                    ##самое левое наслаивание по отношению к ошибке уходит в overlap1:
                    overlap1.append(overlaps[0])
                    ##сама ошибка уходит в overlap2:
                    overlap2.append(indices[i])
        ## на выход:
        ## наложения - словарь - индекс начала: индексы концов
        ## пересечения1 и пересечения 2 - аннотации, которые пересекаются, идут отдельно
        return embedded, overlap1, overlap2
        
    def tackle_embeddings(self,dic):
        b = dic.get('Index')[0]
        ##записываем в emb_errors ошибки, область которых меньше данной:
        emb_errors = [x for x in self.current_doc_errors.items() if (x[1]['Index'] in self.embedding[str(dic.get('Index'))]) and ('Right' in x[1])]
        new_wrong = ''
        nw = 0
        ignore = []
        for j,ws in enumerate(dic['Wrong']):
            emb_intersects = []
            for t,e in emb_errors:
                if e['Index'][0]-b == j:
                    if 'Right' in e and 'Right' in dic and e['Right'] == dic['Right']:
                        break
                    for t1, e1 in emb_errors:
                        if str(e['Index']) in self.embedding[str(e1['Index'])]:
                            ignore += self.embedding[str(e['Index'])]
                            break
                    # if str(e['Index']) in self.embedding:
                    #     ignore += self.embedding[str(e['Index'])]
                    if e['Index'] in self.error_intersects:
                        emb_intersects.append((int(t[1:]),e))
                        continue
                    if e['Index'] not in ignore:
                        if 'Right' in e:
                            new_wrong += e['Right']
                            nw = len(e['Wrong'])
                        elif 'Delete' in e:
                            nw = len(e['Wrong'])
            if emb_intersects:
                emb_intersects = sorted(emb_intersects,key=lambda x: x[0])
                ##а что если попробовать брать самый важный, а не самый последний поставленный тег для аннотаций, область которых совпадает?
                ##лучше этого не делать, можут аолучиться жуть:
                # emb_intersects = sorted(emb_intersects,key=lambda x: self.get_hierarchy(x[1]['Error']))
                last = emb_intersects[-1][1]
                L = -1
                while 'Right' not in last and abs(L)<len(emb_intersects):
                    L -= 1
                    last = emb_intersects[L][1]
                new_wrong += last['Right']
                nw = len(last['Wrong'])
            if not nw:
                new_wrong += ws
            else:
                nw -= 1
        return new_wrong

    def find_overlap(self,s1,s2):
        m = difflib.SequenceMatcher(None, s1, s2).get_matching_blocks()
        if len(m) > 1:
            for x in m[:-1]:
                if x.b == 0:
                    return x.size
        return 0
            

    def make_one_file(self, filename, new_filename):
        """
        Makes file with current types of errors. all other errors checked.
        :param filename: name of the textfile
        return: nothing. just write files in dir <<processed_texts>>
        """
        with open(filename+'.txt', 'r', encoding='utf-8') as text_file:
            self.save_processed(text_file.read(), output_filename = self.path_new+new_filename)
                
    def add_to_processed_list(self, filename = None, meta=None):
        if self.mode != 'direct_input':
            with io.open(filename+'.txt', 'r', newline='', encoding='utf-8') as text_file:
                text = self.save_processed(text_file.read(), output_filename=filename)
        else:
            text = self.save_processed(self.text)
        processed_text = testmaker_utils.ProcessedText(text=text,
        **meta)
        self.processed_texts.append(processed_text)

    def save_processed(self, one_text, output_filename = None):
        processed = ''
        not_to_write_sym = 0
        for i, sym in enumerate(one_text):
            ##идём по каждому символу оригинального текста эссе:
            intersects = []
            ##перебираем все ошибки в этом эссе
            for t_key, dic in self.current_doc_errors.items():
                ##если начало какой-либо ошибки приходится на текущий символ:
                if dic.get('Index')[0] == i:
                    dic['from_last_dot'] =  dic.get('Index')[0] - one_text[:i].rfind('.') - 1
                    ##если исправление попало в меньшую область ошибки - не берём его:
                    if dic.get('Index') in self.embedded:
                        continue
                    ##если исправление попало в большую (закрывающую) область ошибки - берём:
                    if str(dic.get('Index')) in self.embedding:
                        if self.to_include(dic):
                            new_wrong = self.tackle_embeddings(dic)
                            processed += '<<'+str(dic.get('Right'))+'**'+str(t_key)+'**'+str(dic.get('Error'))+'**'+str(dic.get('Relation'))+'**'+str(len(new_wrong))+'**'+new_wrong+'>>'
                            ##устанавливаем, сколько итераций мы не будем дописывать символы:
                            not_to_write_sym = len(dic['Wrong'])
                            break

                    ##если среди пересечений, которые идут раньше
                    if dic.get('Index') in self.overlap1:
                        if not self.to_include(dic):
                            overlap2_ind = self.overlap2[self.overlap1.index(dic.get('Index'))]
                            overlap2_err = [x for x in self.current_doc_errors.values() if x['Index'] == overlap2_ind][-1]
                            if 'Right' in dic and 'Right' in overlap2_err:
                                ##находим число совпадающих элементов в пересекающихся ошибках:
                                rn = self.find_overlap(dic['Right'],overlap2_err['Right'])
                                ##разница правой границы первого и левой границы второго:
                                wn = dic['Index'][1] - overlap2_err['Index'][0]
                                ##разница между длиной первого и предыдущей разницей:
                                indexes_comp = dic.get('Index')[1] - dic.get('Index')[0] - wn
                                if rn == 0:
                                    processed += str(dic.get('Right'))+'#'+str(indexes_comp)+'#'+str(dic.get('Wrong'))[:-wn]
                                else:
                                    processed += str(dic.get('Right')[:-rn])+'#'+str(indexes_comp)+'#'+str(dic.get('Wrong'))[:-wn]
                                not_to_write_sym = len(str(dic.get('Wrong'))) - wn
                                break

                    ##если среди пересечений, которые идут позже:
                    if dic.get('Index') in self.overlap2:
                        overlap1_ind = self.overlap1[self.overlap2.index(dic.get('Index'))]
                        overlap1_err = [x for x in self.current_doc_errors.values() if x['Index'] == overlap1_ind][-1]
                        if self.to_include(overlap1_err):
                            if not self.to_include(dic):
                                if 'Right' in dic and 'Right' in overlap1_err:
                                    rn = self.find_overlap(overlap1_err['Right'],dic['Right'])
                                    ##разница правой границы первого и левой границы второго
                                    wn = overlap1_err['Index'][1] - dic['Index'][0]
                                    indexes_comp = dic.get('Index')[1] - dic.get('Index')[0] - wn
                                    processed += dic.get('Wrong')[:wn] + dic.get('Right')[rn:] +'#'+str(indexes_comp)+ '#'+dic.get('Wrong')[wn:]
                                    # not_to_write_sym = len(str(dic.get('Wrong')))
                            break
                            
                            
                    if dic.get('Index') in self.error_intersects:
                        intersects.append((int(t_key[1:]),dic))
                        continue

                    if dic.get('Right'):
                        indexes_comp = dic.get('Index')[1] - dic.get('Index')[0]
                        if self.to_include(dic):
                            processed += '<<'+str(dic.get('Right'))+'**'+str(t_key)+'**'+str(dic.get('Error'))+'**'+str(dic.get('Relation'))+'**'+str(indexes_comp)+'**'+str(dic.get('Wrong'))+'>>'
                            not_to_write_sym = len(str(dic.get('Wrong')))
                        else:
                            processed += dic.get('Right') +'#'+str(indexes_comp)+ '#'
                    else:
                        if dic.get('Delete'):
                            indexes_comp = dic.get('Index')[1] - dic.get('Index')[0]
                            processed += "#DELETE#"+str(indexes_comp)+"#"
                            
            if intersects:
                intersects = sorted(intersects,key=lambda x: x[0])
                intersects = [x[1] for x in intersects]
                needed_error_types = [x for x in intersects if self.to_include(x)]
                if needed_error_types and 'Right' in needed_error_types[-1]:
                    ## из входящих друг в друга тегов берётся самый верхний:
                    saving = needed_error_types[-1]
                    intersects.remove(saving)
                    if intersects:
                        to_change = intersects[-1]
                        not_to_write_sym = saving['Index'][1] - saving['Index'][0]
                        if 'Right' not in to_change or to_change['Right'] == saving['Right']:
                            indexes_comp = saving['Index'][1] - saving['Index'][0]
                            processed += '<<'+str(saving['Right'])+'**'+str(t_key)+'**'+str(saving['Error'])+'**'+str(saving['Relation'])+'**'+str(indexes_comp)+'**'+saving['Wrong']+'>>'
                        else: 
                            indexes_comp = len(to_change['Right'])
                            processed += '<<'+str(saving['Right'])+'**'+str(t_key)+'**'+str(saving['Error'])+'**'+str(saving['Relation'])+'**'+str(indexes_comp)+'**'+to_change['Right']+'>>'
                else:
                    if 'Right' in intersects[-1]:
                        if len(intersects) > 1 and 'Right' in intersects[-2]:
                            indexes_comp = len(intersects[-2]['Right'])
                            not_to_write_sym = intersects[-1]['Index'][1] - intersects[-1]['Index'][0]
                            processed += intersects[-1]['Right'] + '#'+str(indexes_comp)+ '#' + intersects[-2]['Right']
                        else:
                            indexes_comp = intersects[-1]['Index'][1] - intersects[-1]['Index'][0]
                            processed += intersects[-1]['Right'] + '#'+str(indexes_comp)+ '#'
            if not not_to_write_sym:
                processed += sym
            else:
                not_to_write_sym -= 1
        if not self.use_ram:
            # print('Saving processed text to ', output_filename)
            with open(output_filename+'.txt', 'w', encoding='utf-8') as new_file:
                new_file.write(processed)
        else:
            # print(processed)
            return processed
        
        
    # ================Write Exercises to the files=================


    def check_headform(self, word):
        """Take initial fowm - headform of the word"""
        for key, value in self.wf_dictionary.items():
            headword = [val for val in value if val == word]
            if len(headword)>0:
                return key

    def create_short_answer_ex(self, sent, wrong, right_answer, lb, rb):
            if self.bold:
                new_sent = sent[:lb] + '<b>' + wrong + '</b>' + sent[rb:]
            else:
                new_sent = sent[:lb] + wrong + sent[rb:]
            answers = [right_answer]
            return new_sent, answers

    def create_word_form_ex(self, sent, wrong, right_answer, lb, rb):
        new_sent = sent[:lb] + "{1:SHORTANSWER:=%s}" % right_answer + ' (' +\
                                    self.check_headform(right_answer) + ')' + sent[rb:]
        answers = [right_answer]
        return new_sent, answers

    def create_open_cloze_ex(self, sent, wrong, right_answer, lb, rb):
        new_sent = sent[:lb] + "{1:SHORTANSWER:=%s}" % right_answer + sent[rb:]
        answers = [right_answer]
        return new_sent, answers


    def correct_all_errors(self, sent):
        sent = sent.split('<<')
        corrected_sent = ''
        for i in sent:
            if '>>' in i:
                right = i.split('**')[0]
                corrected_sent += right + i[i.find('>>')+2:]
            else:
                corrected_sent += i
        return corrected_sent

    def create_sentence_function(self, new_text, lengths, meta):
        """
        Makes sentences and write answers for all exercise types
        :return: array of good sentences. [ (sentences, [right_answer, ... ]), (...)]
        """

        def build_exercise_text(text, answers, ex_type, index=None, single_question = False, error_tag = None):
            # if sent1 and sent3 and self.context: # fixed sentences beginning with a dot
            #     text = correct_all_errors(sent1) + '. ' + new_sent + ' ' + correct_all_errors(sent3) #+ '.'
            # elif sent3 and self.context:
            #     text = new_sent + ' ' + correct_all_errors(sent3) #+ '.'
            # else:
            #     text = new_sent
            text = re.sub(' +',' ',text)
            text = re.sub('[а-яА-ЯЁё]+','',text)
            if self.maintain_log:
                question_log = {"ex_type":ex_type,"text":text,"answers":answers,"to_skip":to_skip,"result":"not included"}
            if ('<<' not in text and '>>' not in text):
                if (not to_skip) and (answers != []):
                    if self.show_messages:
                        print('text, answers: ', text, answers)
                    if self.maintain_log:
                        question_log["result"] = "ok"
                    if not index:
                        good_sentences[ex_type].append((text, answers, single_question, error_tag, meta))
                    else:
                        good_sentences[ex_type+'_variant'+str(index)].append((text, answers, single_question, error_tag, meta))
                        self.c0 += 1
                elif to_skip:
                    # if self.show_messages:
                    print('text and answers arent added cause to_skip = True: ', text, answers)
                else:
                    self.c2 -= 1
            else:
                print(text)
                # if self.show_messages:
                print('text and answers arent added cause << or >> in text - probably sentence tokenization issue: ', text, answers)
            if self.maintain_log:
                self.log.append(question_log)

        if self.make_two_variants:
            good_sentences = {x:list() for x in self.output_file_names}
        else:
            good_sentences = {x:list() for x in self.exercise_types}
        types1 = [i for i in self.exercise_types if i!='word_form']
        types2 = [i for i in types1 if i!='multiple_choice']
        sentences = self.sent_tokenize_processed(new_text)
        if self.context:
            context_sentences = []
            ##исправлять ошибки в контексте перед стадией поиска ошибок
            sent_id = 1
            while sent_id < len(sentences)-1:
                if '<<' in sentences[sent_id]:
                    context_sentences.append(self.correct_all_errors(sentences[sent_id-1])+
                    sentences[sent_id] + self.correct_all_errors(sentences[sent_id+1]))
                    sent_id += 2
                else:
                    sent_id += 1
            sentences = context_sentences
        var1 = True
        for sent2 in sentences:
            # c += 1
            single_error_in_sent = False
            to_skip = False
            if '<<' in sent2:
                if self.filter_query:
                    if not re.search(self.filter_query, sent2):
                        continue
                if self.keep_all_exercises and self.exercise_types == ['short_answer']:
                    error_areas = re.finditer("<<.*?>>", sent2)
                    for area in error_areas:
                        try:
                            right_answer, err_index, err_type, relation, index, wrong = area.group(0).strip('<>').split('**')
                            new_sent = self.correct_all_errors(sent2[:area.start(0)]) + '<b>' + wrong + '</b>' + self.correct_all_errors(sent2[area.end(0):])
                            self.c1 += 1
                            build_exercise_text(new_sent, [right_answer], ex_type='short_answer', error_tag=err_type)
                        except:
                            print(sent2)
                else:
                    random.seed(42)
                    ex_type = random.choice(self.exercise_types)
                    if sent2.count('<<') == 1:
                        if self.make_two_variants:
                            single_error_in_sent = True
                        lb = sent2.find('<<')+2
                        rb = sent2.find('>>')
                        correction = sent2[lb:rb]
                        lb -= 2
                        rb += 2
                        if correction.count('**') == 5:
                            right_answer, err_index, err_type, relation, index, wrong = correction.split('**')
                        else:
                            print("'"+correction+"'")
                            continue
                        new_sent, answers = '', []
                        if ex_type == 'word_form':
                            try:
                                new_sent, answers = self.create_word_form_ex(sent2, wrong, right_answer, lb, rb)
                            except:
                                if len(types1) > 0:
                                    random.seed(42)
                                    ex_type = random.choice(types1) 
                                else:
                                    continue
                        if ex_type == 'short_answer':
                            new_sent, answers = self.create_short_answer_ex(sent2, wrong, right_answer, lb, rb)
                        if ex_type == 'open_cloze':
                            new_sent, answers = self.create_open_cloze_ex(sent2, wrong, right_answer, lb, rb)
                    elif sent2.count('<<')>1:
                        # ## вот здесь работаем с предложениями, где больше одной ошибки
                        # ## сюда имплементируй иерархию тегов:
                        n = sent2.count('<<')
                        new_sent,answers = '',[]
                        if self.make_two_variants and (ex_type=='short_answer' or ex_type=='multiple_choice'):
                            new_sent2, answers2 = '',[]
                        split_sent = sent2.split('<<')
                        split_sent = [split_arrows(i.split('**')) if '>>' in i else i for i in split_sent ]
                        if ex_type=='short_answer' or ex_type=='multiple_choice':
                            if not self.hier_choice:
                                chosen = random.randint(0,n-1)
                                if self.make_two_variants:
                                    other_err_ids = list(range(0,n))
                                    other_err_ids.pop(chosen)
                                    random.seed(42)
                                    chosen2 = random.choice(other_err_ids)
                            else:
                                err_types = list(enumerate(split_sent))
                                err_types = [(i[0],i[1][2]) for i in err_types if type(i[1]) == list]
                                err_types = sorted(err_types, key = lambda x: self.get_hierarchy(x[1]), reverse = True) ##сортируем порядковые номера (по нахождению в тексте слева направо тегов
                                ##ошибок в согласии с иерархией тегов ошибок)
                                chosen = err_types[0][0]
                                answers = [split_sent[chosen][0]]
                                if self.make_two_variants:
                                    if split_sent[chosen][3] == 'Parallel_construction':
                                        chosen2 = err_types[1][0]
                                    else:
                                        chosen2 = -1
                                        for i in err_types:
                                            if split_sent[i[0]][3]=='Parallel_construction' and split_sent[i[0]][0]==split_sent[chosen][0]:
                                                continue
                                            else:
                                                chosen2 = i[0]
                                        if chosen2 == -1:
                                            if self.exclude_repeated:
                                                continue
                                            else:
                                                chosen2 = err_types[1][0]
                                    answers2 = [split_sent[chosen2][0]]
                        else:
                            single_error_in_sent = True
                                # print(chosen, chosen2)
                        # split_sent = [{'right_answer':i[0],'err_index':i[1],'err_type':i[2],
                        # 'relation':i[3],'index':i[4],'wrong':i[5].split('>>')[0], 'other':i[5].split('>>')[1]} if len(i)>1 else i for i in split_sent]
                        # print(chosen, len(split_sent))
                        for i in range(len(split_sent)):
                            if not to_skip:
                                # sent, right_answer, err_type, relation, index, other = split_sent[i],split_sent[i+1],split_sent[i+2],split_sent[i+3],split_sent[i+4],split_sent[i+5]
                                if type(split_sent[i]) == list:
                                    # right_answer,err_index,index,relation,wrong, other = split_sent[i]['right_answer'],split_sent[i]['err_index'],split_sent[i]['index'],split_sent[i]['relation'],split_sent[i]['wrong'],split_sent[i]['other']
                                    ## вот здесь причина бага с error_type - переменная обновляется на каждой итерации, а не только тогда, когда i == chosen:
                                    right_answer, err_index, err_type, relation, index, wrong, other = split_sent[i]
                                else:
                                    new_sent += split_sent[i]
                                    if self.make_two_variants and (ex_type == 'short_answer' or ex_type == 'multiple_choice'):
                                        new_sent2 += split_sent[i]
                                    continue
                                # print('/'.join([sent, err_index, right_answer, err_type, relation, index, other]))
                                # input()
                                # try:
                                #     index = int(index)
                                # except:
                                #     to_skip = True
                                #     # print('index: ', index)
                                #     continue
                                if ex_type == 'open_cloze' or ex_type == 'word_form':
                                    right_answer, err_index, err_type, relation, index, wrong, other = split_sent[i]
                                    if ex_type == 'open_cloze':
                                        new_sent += "{1:SHORTANSWER:=%s}" % right_answer + other
                                        answers.append(right_answer)
                                    elif ex_type == 'word_form':
                                        try:
                                            new_sent += "{1:SHORTANSWER:=%s}" % right_answer + ' (' +\
                                                self.check_headform(right_answer) + ')' + other
                                            answers.append(right_answer)
                                        except:
                                            new_sent += right_answer + other
                                else:
                                    if i == chosen:
                                        right_answer, err_index, err_type, relation, index, wrong, other = split_sent[i]
                                        if self.make_two_variants:
                                            new_sent2 += right_answer + other
                                        if ex_type == 'short_answer':
                                            if self.bold:
                                                new_sent += '<b>' + wrong + '</b>' + other
                                            else:
                                                new_sent += wrong + other
                                            # print(right_answer)
                                    else:
                                        if relation == 'Parallel_construction' and right_answer == split_sent[chosen][0]:
                                            if ex_type == 'short_answer':
                                                if self.bold:
                                                    new_sent += '<b>' + wrong + '</b>' + other
                                                else:
                                                    new_sent += wrong + other
                                            elif ex_type == 'multiple_choice':
                                                new_sent += "_______ " + other
                                        else:
                                            new_sent += right_answer + other
                                        if self.make_two_variants:
                                            if i==chosen2:
                                                if ex_type == 'short_answer':
                                                    if self.bold:
                                                        new_sent2 += '<b>' + wrong + '</b>' + other
                                                    else:
                                                        new_sent2 += wrong + other
                                                    answers2 = [right_answer]
                                            else:
                                                if relation == 'Parallel_construction' and right_answer == split_sent[chosen2][0]:
                                                    if ex_type == 'short_answer':
                                                        if self.bold:
                                                            new_sent2 += '<b>' + wrong + '</b>' + other
                                                        else:
                                                            new_sent2 += wrong + other
                                                    elif ex_type == 'multiple_choice':
                                                        new_sent2 += "_______ " + other
                                                else:
                                                    new_sent2 += right_answer + other
                        
                        # continue    
                    if self.make_two_variants:  
                        if ex_type in ('short_answer','multiple_choice'):
                            if single_error_in_sent:
                                ## The variable "split_sent" does not exist in
                                ## context of single error in sentence. However,
                                ## these variables exist here:
                                ## right_answer, err_index, err_type, relation, index, wrong
                                self.c1 += 1
                                # print(self.c1, self.c2)
                                # print(var1)
                                if self.exclude_repeated:
                                    if lengths[ex_type+'_variant1'] > lengths[ex_type+'_variant2']:
                                        var1 = False
                                    elif lengths[ex_type+'_variant1'] < lengths[ex_type+'_variant2']:
                                        var1 = True
                                    
                                    if var1==True:
                                        build_exercise_text(new_sent, answers, ex_type, 1, single_error_in_sent, err_type)
                                        if answers and not to_skip:
                                            lengths[ex_type+'_variant1'] += 1
                                    else:
                                        build_exercise_text(new_sent, answers, ex_type, 2, single_error_in_sent, err_type)
                                        if answers and not to_skip:
                                            lengths[ex_type+'_variant2'] += 1
                                else:
                                    build_exercise_text(new_sent,answers, ex_type, 1, single_error_in_sent, err_type)
                                    build_exercise_text(new_sent,answers, ex_type, 2, single_error_in_sent, err_type)
                            else:
                                self.c2 += 2
                                # print(self.c1, self.c2)
                                build_exercise_text(new_sent,answers, ex_type, 1, single_error_in_sent, split_sent[chosen][2])
                                build_exercise_text(new_sent2,answers2, ex_type, 2, single_error_in_sent, split_sent[chosen2][2])
                                if not to_skip:
                                    if answers:
                                        lengths[ex_type+'_variant1'] += 1
                                    if answers2:
                                        lengths[ex_type+'_variant2'] += 1
                        else:
                            self.c1 += 1
                            # print(self.c1, self.c2)
                            if self.exclude_repeated:
                                if lengths[ex_type+'_variant1'] > lengths[ex_type+'_variant2']:
                                    var1 = False
                                elif lengths[ex_type+'_variant1'] < lengths[ex_type+'_variant2']:
                                    var1 = True
                                
                                if var1==True:
                                    lengths[ex_type+'_variant1'] += 1
                                    build_exercise_text(new_sent, answers, ex_type, 1, single_error_in_sent)
                                else:
                                    lengths[ex_type+'_variant2'] += 1
                                    build_exercise_text(new_sent, answers, ex_type, 2, single_error_in_sent)
                            else:
                                build_exercise_text(new_sent,answers, ex_type, 1, single_error_in_sent)
                                build_exercise_text(new_sent,answers, ex_type, 2, single_error_in_sent)            
                    else:
                        self.c1 += 1
                        # print(self.c1, self.c2)
                        if sent2.count('<<') == 1:
                            build_exercise_text(new_sent,answers, ex_type=ex_type, single_question = single_error_in_sent, error_tag = err_type)
                        else:
                            if ex_type in ('short_answer', 'multiple_choice'):
                                build_exercise_text(new_sent,answers,ex_type=ex_type, single_question=single_error_in_sent, error_tag=split_sent[chosen][2])
                            else:
                                build_exercise_text(new_sent,answers,ex_type=ex_type,single_question=single_error_in_sent)
        return good_sentences

    def write_sh_answ_exercise(self, sentences, ex_type):
        pattern = '<question type="shortanswer">\n\
                    <name>\n\
                    <text>Grammar realec. Short answer {}</text>\n\
                     </name>\n\
                <questiontext format="html">\n\
                <text><![CDATA[{}]]></text>\n\
             </questiontext>\n\
        <answer fraction="100">\n\
        <text><![CDATA[{}]]></text>\n\
        <feedback><text>Correct!</text></feedback>\n\
        </answer>\n\
        </question>\n'
        if self.file_output:
            with open(self.output_file_names[ex_type]+'.xml', 'w', encoding='utf-8') as moodle_ex:
                moodle_ex.write('<quiz>\n')
                for n, ex in enumerate(sentences):
                    moodle_ex.write((pattern.format(n, ex[0], ex[1][0])).replace('&','and'))
                moodle_ex.write('</quiz>')
            if self.write_txt:
                with open(self.output_file_names[ex_type]+'.txt', 'w', encoding='utf-8') as plain_text:
                    for ex in sentences:
                        plain_text.write(ex[1][0]+'\t'+ex[0]+'\n\n')
        else:
            moodle_ex = io.BytesIO()
            moodle_ex.write('<quiz>\n'.encode('utf-8'))
            for n, ex in enumerate(sentences):
                moodle_ex.write((pattern.format(n, ex[0], ex[1][0])).replace('&','and').encode('utf-8'))
            moodle_ex.write('</quiz>'.encode('utf-8'))
            self.output_objects[ex_type+'_xml'] = moodle_ex
            if self.write_txt:
                plain_text = io.BytesIO()
                for ex in sentences:
                    plain_text.write(ex[1][0]+'\t'+ex[0]+'\n\n'.encode('utf-8'))
                self.output_objects[ex_type+'_txt'] = plain_text

    def write_multiple_ch(self, sentences, ex_type):
        pattern = '<question type="multichoice">\n \
        <name><text>Grammar realec. Multiple Choice question {} </text></name>\n \
        <questiontext format = "html" >\n <text> <![CDATA[ <p> {}<br></p>]]></text>\n</questiontext>\n\
        <defaultgrade>1.0000000</defaultgrade>\n<penalty>0.3333333</penalty>\n\
        <hidden>0</hidden>\n<single>true</single>\n<shuffleanswers>true</shuffleanswers>\n\
        <answernumbering>abc</answernumbering>\n<correctfeedback format="html">\n\
        <text>Your answer is correct.</text>\n</correctfeedback>\n\
        <partiallycorrectfeedback format="html">\n<text>Your answer is partially correct.</text>\n\
        </partiallycorrectfeedback>\n<incorrectfeedback format="html">\n\
        <text>Your answer is incorrect.</text>\n</incorrectfeedback>\n'
        if self.file_output:
            with open(self.output_file_names[ex_type]+'.xml', 'w', encoding='utf-8') as moodle_ex:
                moodle_ex.write('<quiz>\n')
                for n, ex in enumerate(sentences):
                    moodle_ex.write((pattern.format(n, ex[0])).replace('&','and'))
                    for n, answer in enumerate(ex[1]):
                        correct = 0
                        if n == 0:
                            correct = 100
                        moodle_ex.write('<answer fraction="{}" format="html">\n<text><![CDATA[<p>{}<br></p>]]>'
                                        '</text>\n<feedback format="html">\n</feedback>\n</answer>\n'.format(correct, answer))
                    moodle_ex.write('</question>\n')
                moodle_ex.write('</quiz>')
            if self.write_txt:
                with open(self.output_file_names[ex_type]+'.txt', 'w',encoding='utf-8') as plain_text:
                    for ex in sentences:
                        plain_text.write(ex[0] + '\n' + '\t'.join(ex[1]) + '\n\n')
        else:
            moodle_ex = io.BytesIO()
            moodle_ex.write('<quiz>\n'.encode('utf-8'))
            for n, ex in enumerate(sentences):
                moodle_ex.write((pattern.format(n, ex[0])).replace('&','and').encode('utf-8'))
                for n, answer in enumerate(ex[1]):
                    correct = 0
                    if n == 0:
                        correct = 100
                    moodle_ex.write('<answer fraction="{}" format="html">\n<text><![CDATA[<p>{}<br></p>]]>'
                                    '</text>\n<feedback format="html">\n</feedback>\n</answer>\n'.format(correct,
                                     answer).encode('utf-8'))
                moodle_ex.write('</question>\n'.encode('utf-8'))
            moodle_ex.write('</quiz>'.encode('utf-8'))
            self.output_objects[ex_type+'_xml'] = moodle_ex
            if self.write_txt:
                plain_text = io.BytesIO()
                for ex in sentences:
                    plain_text.write(ex[0] + '\n' + '\t'.join(ex[1]) + '\n\n'.encode('utf-8'))
                self.output_objects[ex_type+'_txt'] = plain_text

    def write_open_cloze(self, sentences, ex_type):
        """:param type: Word form or Open cloze"""
        type = ''
        if ex_type == 'word_form':
            type = "Word form"
        elif ex_type == 'open_cloze':
            type = "Open Cloze"
        pattern = '<question type="cloze"><name><text>Grammar realec. {} {}</text></name>\n\
                     <questiontext format="html"><text><![CDATA[<p>{}</p>]]></text></questiontext>\n''<generalfeedback format="html">\n\
                     <text/></generalfeedback><penalty>0.3333333</penalty>\n\
                     <hidden>0</hidden>\n</question>\n'
        if self.file_output:
            with open(self.output_file_names[ex_type]+'.xml','w', encoding='utf-8') as moodle_ex:
                moodle_ex.write('<quiz>\n')
                for n, ex in enumerate(sentences):
                    moodle_ex.write((pattern.format(type, n, ex[0])).replace('&','and'))
                moodle_ex.write('</quiz>')
            if self.write_txt:
                with open(self.output_file_names[ex_type]+'.txt','w', encoding='utf-8') as plain_text:
                    for ex in sentences:
                        plain_text.write(ex[0]+'\n\n')
        else:
            moodle_ex = io.BytesIO()
            moodle_ex.write('<quiz>\n'.encode('utf-8'))
            for n, ex in enumerate(sentences):
                moodle_ex.write((pattern.format(type, n, ex[0])).replace('&','and').encode('utf-8'))
            moodle_ex.write('</quiz>'.encode('utf-8'))
            self.output_objects[ex_type+'_xml'] = moodle_ex
            if self.write_txt:
                plain_text = io.BytesIO()
                for ex in sentences:
                    plain_text.write(ex[0] + '\n' + '\t'.join(ex[1]) + '\n\n'.encode('utf-8'))
                self.output_objects[ex_type+'_txt'] = plain_text

    def test_tokenizing(self):
        for file in os.listdir(self.path_new):
            with open(os.path.join(self.path_new, file),'r',encoding='utf-8') as f:
                text = f.read()
            self.sent_tokenize_processed(text)
    
    def make_exercise(self):
        """Write it all in moodle format and txt format"""
        print('Making exercises...')
        if self.make_two_variants:
            all_sents = {x:list() for x in self.output_file_names}
        else:
            all_sents = {x:list() for x in self.exercise_types}
        
        if self.use_ram:
            list_to_iter = self.processed_texts
        else:
            list_to_iter = testmaker_utils.ProcessedTextFileIter(self.path_new)
        self.c1 = 0
        self.c2 = 0
        self.c0 = 0 # сколько всего предложений с ошибкой прошло функцию build_exercise_text()
        if self.tqdm:
            list_to_iter = tqdm_notebook(list_to_iter, total=len(list_to_iter))
        for one_doc in list_to_iter:
            new_text = ''
            text_array = one_doc.text.split('#')
            current_number = 0
            for words in text_array:
                words = words.replace('\n', ' ').replace('\ufeff', '')
                if re.match('^[0-9]+$', words):
                    if words != '':
                        current_number = int(words)
                elif words == 'DELETE':
                    current_number = 0
                else:
                    new_text += words[current_number:]
                    current_number = 0
            if '<<' in new_text:
                new_sents = self.create_sentence_function(new_text, {i:len(all_sents[i]) for i in all_sents}, one_doc.meta)
                for key in all_sents:
                    # print(len(all_sents[key]), end = ' ')
                    all_sents[key] += new_sents[key]
                # print()
        
        for key in all_sents:
            print('Writing '+key+' questions, '+str(len(all_sents[key]))+' total ...')
            if self.moodle_output:
                if '_variant' in key:
                    ex_type = '_'.join(key.split('_')[:-1])
                    self.write_func[ex_type](all_sents[key],key)
                else:
                    self.write_func[key](all_sents[key],key)
            else:
                self.output_objects = all_sents
        if not self.use_ram:
            if not self.keep_processed:
                shutil.rmtree('./processed_texts/')

        if self.maintain_log:
            self.write_log()
        if self.file_output:
            print('done, saved to: ' + self.output_path)
        else:
            print('done, saved in RAM as BytesIO object')

    def write_log(self):
        path_to_save = self.output_path+os.sep + '{}log.csv'.format(self.log_name)
        with open(path_to_save,'w',encoding='utf-8') as l:
            writer = csv.DictWriter(l,self.fieldnames)
            writer.writeheader()
            writer.writerows(self.log)
            print ('log saved to: ', path_to_save)

def main(path_to_data = None,exercise_types = None,output_path = None,error_types = None,mode = 'direct_input',
context = True, maintain_log = True, show_messages = False, bold = True, use_ram = False, ann = None, text =None,
make_two_variants = False, exclude_repeated = False, hier_choice = True):
    e = Exercise(path_to_realecdata = path_to_data, exercise_types = exercise_types, output_path = output_path,
     ann = ann, text = text, error_types = error_types, bold=bold, context=context,mode=mode, maintain_log=maintain_log,
     show_messages=show_messages,use_ram = use_ram,
     keep_all_exercises=False,
     make_two_variants = make_two_variants,
     exclude_repeated=exclude_repeated, keep_processed = True, hier_choice = hier_choice)
    e.make_data_ready_4exercise()
    # e.test_tokenizing()
    ## commented out for testing purposes:
    e.make_exercise()
    ## for debugging purposes:
    # print(e.c1, e.c2, e.c0)

def console_user_interface():
    print('Welcome to REALEC English Test Maker!')
    print('''2016-2018, Russian Error-Annotated Learners' of English Corpus research group,
HSE University,
Moscow.
''')
    path_to_collection = input('Enter path to collection in REALEC corpus (default - collection "/exam/"): ').strip()
    path_to_data = input('Enter path to store corpus data (default - texts will be downloaded to current folder):    ').strip()
    exercise_types = input('Enter exercise types (short_answer, word_form, open_cloze) separated by gap:    ').lower().split()
    error_types = input('Enter error types separated by gap (default - all error tags will be included):    ').split()
    output_path = input('Enter path to output files (default - create folder "moodle exercises" in current folder):     ')
    context = input('Do you want to include contexts?  y/n:   ').strip().lower()
    if context == 'y' or 'yes':
        context = True
    else:
        context = False
    from datetime import datetime
    startTime = datetime.now()
    r = realec_helper.realecHelper()
    if not path_to_data:
        path_to_data = '.'
    if not path_to_collection:
        path_to_collection = '/exam/'
    r.download_folder(path_to_folder=path_to_collection, path_to_saved_folder=path_to_data)
    path_to_data = r.path
    main(path_to_data, exercise_types, output_path, error_types,mode='folder',context=context,bold = True,
    make_two_variants=True, hier_choice=True)
    print('finished in '+str(datetime.now() - startTime))

def test_launch():
    error_types = ['Tense_choice','Tense_form','Voice_choice','Voice_form',
                    'Infinitive_constr','Gerund_phrase','Infinitive_with_to',
                    'Infinitive_without_to_vs_participle','Verb_Inf_Gerund',
                    'Verb_part','Verb_Inf','Verb_Bare_Inf','Participial_constr',
                    'Number','Standard','Num_form','Incoherent_tenses','Incoherent_in_cond',
                    'Tautology','lex_part_choice','Prepositional_adjective','Prepositional_noun']
    
    main('./IELTS' ,['open_cloze','short_answer','word_form'], './moodle_exercises/', error_types = error_types, mode='folder')

def test_ideally_annotated():
    for ex_type in ('open_cloze', 'short_answer', 'word_form'):
        for context in (True, False):
            print(ex_type, context)
            main(path_to_data = './ideally_annotated', exercise_types = [ex_type], output_path = './ideally_annoted_output',
             error_types = [], mode='folder', context=context, maintain_log = True, show_messages = False, bold = True)

def test_with_ram():
    for ex_type in ('open_cloze', 'short_answer', 'word_form'):
        for context in (True, False):
            print(ex_type, context)
            main(path_to_data = './test_with_ram_input/AAl_12_2.ann', exercise_types = [ex_type], use_ram = True,
             output_path = './test_with_ram_output_file_input', error_types = [], mode='file', context=context,
              maintain_log = True, show_messages = True, bold = True)

def test_direct_input():
    with open (r'./2nd-year-thesis/realec_dump_31_03_2018/exam/exam2014/DZu_23_2.txt','r',encoding='utf-8') as inp:
        text = inp.read()
    with open (r'./2nd-year-thesis/realec_dump_31_03_2018/exam/exam2014/DZu_23_2.ann','r',encoding='utf-8') as inp:
        ann = inp.read()
    #for ex_type in ('open_cloze', 'short_answer', 'word_form'):
    main(ann=ann, text=text, exercise_types = ['open_cloze', 'short_answer', 'word_form'], use_ram = True,
     output_path = './test_with_direct_input_output_file_input', error_types = [], mode='direct_input', context=False,
      maintain_log = True, show_messages = True, bold = True)

def generate_exercises_from_essay(essay_name, context=False, exercise_types = ['short_answer'],file_output = True, show_messages = False,
 write_txt = False, error_types=[], use_ram = True, output_file_names = None, keep_processed = False, maintain_log = False, hier_choice = False,
 make_two_variants = False, exclude_repeated = False, output_path = 'quizzes', include_smaller_mistakes = True, file_prefix = os.getcwd()+'/',
 moodle_output=True):
    helper = realec_helper.realecHelper()
    helper.download_essay(essay_name, include_json = False, save = False)
    # debugging prints:
    # print(helper.current_text[:100])
    # print(helper.current_ann[:100])
    e = Exercise(ann=helper.current_ann, text=helper.current_text,
     exercise_types = exercise_types, use_ram = use_ram,
     output_path = output_path, error_types = error_types, mode='direct_input', context=context,
     maintain_log = maintain_log, show_messages = show_messages, bold = True, file_output = file_output, write_txt = write_txt, output_file_names = output_file_names,
     keep_processed = keep_processed, hier_choice = hier_choice, make_two_variants = make_two_variants, exclude_repeated = exclude_repeated,
     include_smaller_mistakes = include_smaller_mistakes, file_prefix = file_prefix, moodle_output = False)
    e.make_data_ready_4exercise()
    e.make_exercise()
    if file_output:
        return e.output_file_names
    else:
        return e.output_objects

def test_with_realec_helper():
    # essay_name = '/exam/exam2014/DZu_23_2'
    essay_name = 'http://www.realec.org/index.xhtml#/exam/exam2017/EGe_105_2'
    essay_paths = generate_exercises_from_essay(essay_name)
    print(essay_paths)

def test_with_relations():
    # essay_name = "http://realec.org/index.xhtml#/exam/exam2017/EGe_101_1"
    essay_name = "http://realec.org/index.xhtml#/exam/exam2017/EGe_105_2"
    essay_paths = generate_exercises_from_essay(essay_name, use_ram=False)
    print(essay_paths)

def download_folder_and_make_exercises(folder_name, output_path=None, maintain_log=False,
 error_types=[], context=True, make_two_variants=True, file_output=True, moodle_output=True, check_duplicates=True,
 keep_processed=False,
 path_to_downloaded='downloaded_'+get_fname_time(),
 delete_downloaded=False,
 filter_query=None):
    r = realec_helper.realecHelper()
    r.download_folder(folder_name, path_to_saved_folder=path_to_downloaded)
    if check_duplicates:
        all_texts = set()
        for root, dirs, files in os.walk(r.path):
            for f in files:
                if f.endswith('.txt'):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as inp:
                            essay_text = inp.read()
                        if essay_text in all_texts:
                            os.remove(os.path.join(root, f))
                            essay_anno = os.path.join(root, f[:f.rfind('.')]+'.ann')
                            if os.path.exists(essay_anno):
                                os.remove(essay_anno)     
                        else:
                            all_texts.add(essay_text)
                    except UnicodeDecodeError:
                        os.remove(os.path.join(root, f))
                        essay_anno = os.path.join(root, f[:f.rfind('.')]+'.ann')
                        if os.path.exists(essay_anno):
                            os.remove(essay_anno)
        del all_texts
    exercise_types = ['short_answer']
    # print(error_types)
    e = Exercise(path_to_realecdata = r.path,
    exercise_types=exercise_types, file_output=file_output,
    moodle_output=moodle_output,
    output_path=output_path, error_types=error_types,
    maintain_log=maintain_log,
    mode='folder',context=context,bold = True,
    make_two_variants=make_two_variants,
    hier_choice=True, show_messages=False, keep_processed=keep_processed,
    filter_query=filter_query)
    e.make_data_ready_4exercise()
    e.make_exercise()
    if delete_downloaded:
        shutil.rmtree(path_to_downloaded, ignore_errors=True)
    if file_output:
        return e.output_file_names
    else:
        return e.output_objects


if __name__ == '__main__':
    console_user_interface()
