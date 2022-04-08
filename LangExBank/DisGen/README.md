# DisGen
A generator of options for multiple choice questions derived from REALEC texts

Currently three types of errors are supported:
 - Choice of tense
 - Choice of a lexical item (Verbs only)
 - Prepositions

Choice of tense distractors are derived using rule-based approach with SpaCy language parser, Lexical & Prepositional distractors utilise word-level RNNs.

Repository also includes a web service for obtaining distractors from set of error contexts extracted from REALEC with realec-testmaker both in JSON and MS Excel format. 
