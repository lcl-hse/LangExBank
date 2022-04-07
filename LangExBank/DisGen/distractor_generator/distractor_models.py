import spacy, textdistance, lemminflect
import re

import torch as tt
import pandas as pd

from torchtext.data import Field, LabelField, RawField, BucketIterator, TabularDataset, Iterator
from torchtext.vocab import Vectors

from . import Tenses
from .tense_distractors import *
from .clear_data import *
from .nn_models import *


def select_most_probable(row, answer_cols, inflect=False, skip_list=[], k=5):
    outp = []
    for i in range(1, k+1):
        append = True
        option = row[f'Option {i}']
        for col in answer_cols:
            if option == row[col] or option in skip_list:
                append = False
        if append:
            if inflect:
                try:
                    option = lemminflect.getInflection(option, row['Tag'])[0]
                except:
                    option = option
            outp.append(option)

    if len(outp) < 3:
        for i in range(3-len(outp)):
            outp.append(None)

    outp = outp[:3]
    
    return outp

class DistractorModel(object):
    def __init__(self):
        self.gen_func = lambda x: (None, None, None)
    
    def prepare_data(self, df):
        return df
    
    def postprocess_data(self, df):
        ## Keep only necessary columns:
        # if 'Right answer lemma' in df and 'Wrong answer lemma' in df:
        #     df = df[['Sentence','Right answer','Wrong answer','Distractor 1',
        #              'Distractor 2', 'Distractor 3', 'Error type',
        #              'Right answer lemma', 'Wrong answer lemma']]
        # else:
        cols_to_keep = ['Sentence','Right answer','Wrong answer','Distractor 1','Distractor 2', 'Distractor 3', 'Error type']
        if 'Folder' in df:
            cols_to_keep.append('Folder')
        if 'Filename' in df:
            cols_to_keep.append('Filename')
        df = df[cols_to_keep]
        df['Sentence'] = df['Sentence'].apply(lambda x: re.sub('<b>.*?</b>','_'*8, x))
        return df

    def get_distractors(self, df):
        df = self.prepare_data(df)
        df[['Distractor 1', 'Distractor 2', 'Distractor 3']] = df.apply(self.gen_func,
                                                                        axis=1,
                                                                        result_type="expand")
        return self.postprocess_data(df)

class TenseChoiceModel(DistractorModel):
    def __init__(self, spacy_model_name):
        self.parser = spacy.load(spacy_model_name)
        self.estimator = textdistance.Hamming()
        self.gen_func = lambda x: get_tense_distractors(x, self.estimator, self.parser)
    
    def prepare_data(self, df):
        ## Check that a verb is present in correction:
        df['Contains verb'] = df['Right answer'].apply(lambda x: contains_pos(x, ('VERB','AUX'),self.parser))
        df = df[df['Contains verb']==True]
        df = df.drop(['Contains verb'], axis=1)

        ## Determine right & wrong tense, voice & lemma:
        df['Wrong answer'] = df['Sentence'].apply(find_error)
        df[['Right tense', 'Right voice']] = df.apply(lambda x: Tenses.determine_tense(x['Right answer'], self.parser),
                                                           axis=1, result_type="expand")
        df[['Wrong tense', 'Wrong voice']] = df.apply(lambda x: Tenses.determine_tense(x['Wrong answer'], self.parser),
                                                                axis=1, result_type="expand")
        df[['Wrong answer lemma', 'Right answer lemma']] = df.apply(lambda x: get_lemmas(x, self.parser),
                                axis=1, result_type='expand')

        ## Lemma & voice must match in error and correction, tense must not match:
        df = df[df['Wrong answer lemma'] == df['Right answer lemma']]
        df = df[df['Right voice'] == df['Wrong voice']]
        df = df[df['Right tense'] != df['Wrong tense']]

        ## Check that correction is not a solitary auxiliary:
        df['AUX'] = df.apply(lambda x: is_corr_root_aux(x['Sentence'],
                                                    x['Right answer'],
                                                    self.parser),
                         axis=1)
        df = df[df['AUX'] == False]

        ## Determine person and number:
        df['Person/Number'] = df.apply(lambda x: persn_nmb(x['Sentence'],
                                                        x['Right answer'],
                                                        self.parser), axis=1)
        
        ## Drop unnecessary columns:
        df['Voice'] = df['Right voice']
        df = df.drop(['Right voice','Wrong voice','Right answer lemma','Wrong answer lemma'],
                                axis=1)
        
        ## Determine if the verb is negated:
        df['Neg'] = df['Right answer'].apply(lambda x: determine_polarity(x, self.parser))

        return df

class DualContextRNNModel(DistractorModel):
    def __init__(self, spacy_model_name,
                 question_vocab_dir, answer_vocab_dir,
                 right_answer_col,
                 nn_weights_path, batch_size=128,
                 device = tt.device('cpu')):
        self.parser = spacy.load(spacy_model_name)

        vocab = load_vocab(question_vocab_dir)
        preprocess = lambda x: [i if i in vocab.stoi else '<unk>' for i in x]
        self.TOKENS = Field(lower=True, preprocessing=preprocess)
        self.TOKENS.vocab = load_vocab(question_vocab_dir)

        self.ANSWER = LabelField(dtype=tt.int64, use_vocab=True, unk_token='<unk>')
        self.ANSWER.vocab = load_vocab(answer_vocab_dir)
        #self.ANSWER.vocab.vectors = Vectors(gensim_vectors_path)

        self.device = device
        self.nn_weights_path = nn_weights_path
        self.batch_size = batch_size

        self.model = None
        self.right_answer_col = right_answer_col
    
    def infer(self, df, answer_cols, inflect=False, skip_list=[]):
        df[self.right_answer_col] = df[self.right_answer_col].apply(lambda x: x if x in self.ANSWER.vocab.stoi else '<unk>')
        ds = DataFrameDataset(df, self.TOKENS, self.ANSWER, self.right_answer_col)
        DataIter = BucketIterator(ds, batch_size=self.batch_size)
        model_output = get_k_predicted_items(self.model, DataIter, self.device, self.ANSWER.vocab.itos, k=5)

        all_predictions = []

        for batch in model_output:
            id_batch, item_batch, proba_batch = batch
            for index, items, probas in zip(id_batch, item_batch, proba_batch):
                all_predictions.append({'id':int(index),
                                        'Option 1':items[0],
                                        'Option 2':items[1],
                                        'Option 3':items[2],
                                        'Option 4':items[3],
                                        'Option 5':items[4]})
        
        all_predictions = pd.DataFrame(all_predictions).set_index('id')
        df = pd.concat([df, all_predictions], axis=1, join="inner")

        ## Filter options matching 'answer cols':
        df[['Distractor 1', 'Distractor 2', 'Distractor 3']] = df.apply(lambda x: select_most_probable(x, answer_cols, inflect, skip_list),
                                                                        axis=1, result_type='expand')

        return df

class LexItemChoiceModel(DualContextRNNModel):
    def get_distractors(self, df):
        df = self.prepare_data(df)

        model = W2VErrorModel(vocab_size=len(self.TOKENS.vocab.itos),
                              embed_size=300,
                              hidden1_size=300, hidden2_size=200,
                              output_size=len(self.ANSWER.vocab.itos))
        self.model = model.to(self.device)
        self.model.load_state_dict(tt.load(self.nn_weights_path,
                                           map_location=self.device))

        df = self.infer(df, answer_cols = ('Right answer lemma', 'Wrong answer lemma'), inflect=True)

        return self.postprocess_data(df)
    
    def filter(self, df, pos_to_keep):
        ## Filter:
        df['Wrong answer'] = df['Sentence'].apply(find_error)
        df['Right answer'] = df['Right answer'].str.lower()
        df['Wrong answer'] = df['Wrong answer'].str.lower()
        filter_func_r = lambda x: is_one_word(x['Right answer'], self.parser)
        filter_func_w = lambda x: is_one_word(x['Wrong answer'], self.parser)

        df[['Keep 1','Right answer lemma', 'POS Right', 'Tag Right']] = df.apply(filter_func_r, axis=1,
                                                                                 result_type="expand")
        df[['Keep 2','Wrong answer lemma', 'POS Wrong', 'Tag Wrong']] = df.apply(filter_func_w, axis=1,
                                                                                 result_type="expand")

        df = df[(df['Keep 1'] == True) & (df['Keep 2'] == True)]

        df = df[df['POS Right'] == pos_to_keep]
        df['Tag'] = df['Tag Right']
        df = df.drop(['Keep 1', 'Keep 2','POS Right','POS Wrong', 'Tag Right', 'Tag Wrong'], axis=1)


        ## Split context:
        df[['left','right']] = df.apply(lambda x: remove_err_span(x['Sentence']), axis=1,
                                                  result_type="expand")
        return df

class LexVerbsModel(LexItemChoiceModel):
    def prepare_data(self, df):
        ## Filter:
        verb_df = self.filter(df, pos_to_keep='VERB')
        return verb_df

class LexNounsModel(LexItemChoiceModel):
    def prepare_data(self, df):
        ## Filter:
        noun_df = self.filter(df, pos_to_keep='NOUN')
        return noun_df

class LexAdjModel(LexItemChoiceModel):
    def prepare_data(self, df):
        ## Filter:
        adj_df = self.filter(df, pos_to_keep='ADJ')
        return adj_df

class PrepositionsModel(DualContextRNNModel):
    def prepare_data(self, df):
        df['Right answer'] = df['Right answer'].str.lower()
        df['Wrong answer'] = df['Sentence'].apply(find_error)
        df['Wrong answer'] = df['Wrong answer'].str.lower()

        df['Keep'] = df['Right answer'].apply(lambda x: is_prep(x, self.parser))
        df = df[df['Keep'] == True]
        df = df.drop(['Keep'], axis=1)

        ## Split context:
        df[['left','right']] = df.apply(lambda x: remove_err_span(x["Sentence"]),
                                        axis=1,
                                        result_type="expand")

        df['Right answer'] = df['Right answer'].apply(lambda x: x.lower().strip())

        return df

    def get_distractors(self, df):
        df = self.prepare_data(df)

        model = W2VErrorModel(vocab_size=len(self.TOKENS.vocab.itos),
                              embed_size=300,
                              hidden1_size=200, hidden2_size=150,
                              output_size=len(self.ANSWER.vocab.itos))
        self.model = model.to(self.device)
        self.model.load_state_dict(tt.load(self.nn_weights_path,
                                           map_location=self.device))

        df = self.infer(df, answer_cols=('Right answer', 'Wrong answer'),
                                         inflect=False, skip_list=('of','is'))

        return self.postprocess_data(df)