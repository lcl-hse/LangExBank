from .distractor_models import *

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

tense_choice_init_params = {'spacy_model_name': 'en_core_web_sm'}

prepositions_init_params = {'spacy_model_name': 'en_core_web_sm',
                            'question_vocab_dir': os.path.join(base_path, 'preps_question_vocab'), 
                            'answer_vocab_dir': os.path.join(base_path, 'preps_answer_vocab'),
                            'nn_weights_path': os.path.join(base_path,
                                                            os.path.join('model_weights', 'preps_model')),
                            'right_answer_col': 'Right answer'}

verb_lex_choice_init_params = {'spacy_model_name': 'en_core_web_sm',
                               'question_vocab_dir': os.path.join(base_path, 'verbs_question_vocab'),
                               'answer_vocab_dir': os.path.join(base_path, 'verbs_answer_vocab'),
                               'nn_weights_path': os.path.join(base_path,
                                                               os.path.join('model_weights', 'verbs_lex_model')),
                               'right_answer_col': 'Right answer lemma'}

noun_lex_choice_init_params = {'spacy_model_name': 'en_core_web_sm',
                               'question_vocab_dir': os.path.join(base_path, 'nouns_question_vocab'),
                               'answer_vocab_dir': os.path.join(base_path, 'nouns_answer_vocab'),
                               'nn_weights_path': os.path.join(base_path,
                                                               os.path.join('model_weights', 'nouns_lex_model')),
                               'right_answer_col': 'Right answer lemma'}

adj_lex_choice_init_params = {'spacy_model_name': 'en_core_web_sm',
                               'question_vocab_dir': os.path.join(base_path, 'adj_question_vocab'),
                               'answer_vocab_dir': os.path.join(base_path, 'adj_answer_vocab'),
                               'nn_weights_path': os.path.join(base_path, os.path.join('model_weights','adj_lex_model')),
                               'right_answer_col': 'Right answer lemma'}

distractor_models = [
    ('Tense_choice', (TenseChoiceModel, tense_choice_init_params)),
    ('Prepositions', (PrepositionsModel, prepositions_init_params)),
    ('lex_item_choice', (LexVerbsModel, verb_lex_choice_init_params)),
    ('lex_item_choice', (LexNounsModel, noun_lex_choice_init_params)),
    ('lex_item_choice', (LexAdjModel, adj_lex_choice_init_params)),
]