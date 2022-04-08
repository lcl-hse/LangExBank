import pandas as pd

from .distractor_models import *
from .config import distractor_models
from .Tenses import correct

from spellchecker import SpellChecker
from nltk import word_tokenize

def filter_first(df):
    ## First filter by unknown words:
    unk_max_count = 5
    checker = SpellChecker()
    unk_filter = lambda x: len(checker.unknown(word_tokenize(correct(x['Sentence'], x['Right answer']))))<unk_max_count

    df['Keep'] = df.apply(unk_filter, axis=1)
    df = df[df['Keep'] == True]

    return df

def get_distractors(df):
    df = filter_first(df)
    result_dfs = []
    for error_type, (Model_class, model_init_params) in distractor_models:
        needed_subset = df[df['Error type'] == error_type]
        model = Model_class(**model_init_params)
        try:
            new_df = model.get_distractors(needed_subset)
            result_dfs.append(new_df)
        except ValueError:
            continue
    if result_dfs:
        output_df = pd.concat(result_dfs, axis=0, sort=False)
        output_df.sort_index(inplace=True)
        return output_df
    else:
        return pd.DataFrame()
