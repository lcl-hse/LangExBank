from xml.etree.ElementTree import Element, tostring
from html import unescape

import os
import re

URL_PREFIX = os.getenv(
    "REF_URL_PREFIX",
    default=""
)


tag_map = {
    "suggestion": "Исправление",
    "note": "Комментарий",
    "Related": "Связь",
    "Intransitive": "Intransitive verb",
    "Transitive": "Transitive verb",
    "Reflexive_verb": "Reflexive verb",
    "Ambitransitive": "Ambitransitive verb",
    "Tense_choice": "Choice of tense",
    "Tense_form": "Tense form",
    "Infinitive_with_to": "Infinitive (with/without to)",
    "Infinitive_without_to_vs_participle":
        "Infinitive without to vs. participle",
    "Prepositional_verb": "Prepositional or phrasal verb",
    "Presentation": "Verb with as",
    "Dative": "Dative verb with alternation",
    "Two_in_a_row": "Two verbal forms in the predicate",
    "Verb_Gerund": "Verb + Gerund",
    "Verb_Bare_Inf": "Verb + Bare Infinitive",
    "Verb_Inf": "Verb + Infinitive",
    "Verb_object_bare": "Verb + Object/Addressee + Bare Infinitive",
    "Restoration_alter": "Infinitive Restoration Alternation",
    "Verb_Inf_Gerund": "Verb + Infinitive OR Gerund",
    "Complex_obj": "Complex-object verb",
    "Verb_part": "Verb + Participle",
    "Get_part": "Get + participle",
    "Verbal_idiom": "Verbal idiom",
    "Followed_by_a_clause": "Verb followed by a clause",
    "that_clause": "Verb + that/WH + Clause",
    "if_whether_clause": "Verb + if/whether + clause",
    "that_subj_clause": "Verb + that + Subjunctive clause",
    "it_conj_clause": "Verb + it + Conj + Clause",
    "Participial_constr": "Participial construction",
    "Infinitive_constr": "Infinitive construction",
    "Noun_attribute": "Noun as an attribute",
    "Noun_number": "Noun number",
    "Noun_inf": "Noun + Infinitive",
    "Possessive": "Possessive form of a noun",
    "Adj_as_collective": "Adjective as a collective noun",
    "Comparative_adj": "Comparative degree of adjectives",
    "Superlative_adj": "Superlative degree of adjectives",
    "Comparative_adv": "Comparative degree of adverbs",
    "Superlative_adv": "Superlative degree of adverbs",
    "Prepositional_adv": "Prepositional adverb",
    "Countable_uncountable": "Countable/uncountable",
    "Prepositional_noun": "Prepositional noun",
    "Prepositional_adjective": "Prepositional adjective",
    "Agreement_errors": "Agreement",
    "Abs_comp_clause": "Incomplete sentence",
    "Title_structure": "Title structure",
    "Note_structure": "Note structure",
    "Comparative_constr": "Comparative construction",
    "Numerical": "Numerical comparison",
    "Absence_predicate": "Absence of predicate",
    "Absence_subject": "Absence of subject",
    "Word_order": "Word order",
    "Standard": "Standard word order",
    "Emphatic": "Emphatic shift",
    "Cleft": "Cleft sentence",
    "Interrogative": "Interrogative word order",
    "Word_choice": "Word choice",
    "Relative_clause": "Relative clause",
    "Defining": "Defining relative clause",
    "Non_defining": "Non-defining relative clause",
    "Coordinate": "Coordinate relative clause",
    "Attr_participial": "Attributive participial construction",
    "Lack_par_constr": "Parallel constructions",
    "lex_item_choice": "Choice of lexical item",
    "lex_part_choice": "Choice of a part of lexical item",
    "Often_confused": "Words often confused",
    "Category_confusion": "Confusion of categories",
    "Absence_comp_colloc": "Absence of certain components of a collocation",
    "Redundant": "Redundant word(s)",
    "Derivation": "Word formation",
    "Formational_affixes": "Derivational affixes",
    "Compound_word": "Compound word",
    "Suffix": "Formational suffix",
    "Prefix": "Formational prefix",
    "L1_interference": "Interference of L1",
    "Discourse_error": "Discourse error",
    "Ref_device": "Referential device",
    "Linking_device": "Linking device",
    "Inappropriate_register": "Inappropriate register",
    "Absence_comp_sent": "Absence of a component in clause or sentence",
    "Redundant_comp": "Redundant component in clause or sentence",
    "Absence_explanation": "Absence of necessary explanation or detail",
    "Verb_pattern": "Verb pattern",
    "Gerund_phrase": "Gerund phrase",
    "Confusion_of_structures": "Confusion of structures",
}


def map_tag(tag):
    if tag in tag_map:
        return tag_map[tag]
    else:
        return tag


class Tree:
    def __init__(self, shname=None, fname=None):
        self.shname = shname
        self.fname = fname
        self.children = []

    def append(self, elem):
        self.children.append(elem)


def get_html_taglist():
    with open("annotation.conf.txt", "r", encoding="utf-8") as inp:
        text = inp.read()

    started = False

    tagtree = Tree()

    treeStack = []

    curr_tree = tagtree

    prev_line = ""

    for line in text.splitlines():
        if line == "suggestion":
            started = True
        elif started:
            if line.count("\t") == 0:
                break
            else:
                if line.count("\t") == prev_line.count("\t") + 1:
                    treeStack.append(curr_tree)
                elif line.count("\t") < prev_line.count("\t"):
                    for i in range(prev_line.count("\t") - line.count("\t")):
                        treeStack.pop()
                curr_tree = Tree(line.strip(), map_tag(line.strip()))
                treeStack[-1].append(curr_tree)

        prev_line = line

    return unescape(str(tostring(traverse_tag_tree(tagtree)))[2:-1])


def get_str_taglist():
    with open("annotation.conf.txt", "r", encoding="utf-8") as inp:
        text = inp.read()

    tags = []
    started = False

    for line in text.splitlines():
        if line == "suggestion":
            started = True
            continue
        elif started:
            if line.count("\t") == 0:
                break
            else:
                ident = line.count("\t")
                line = line.strip()
                if line and not (
                    line.startswith("#") or line.startswith("pos_")
                ):
                    short_tag = line
                    line = "&nbsp;" * ident + map_tag(line)
                    tags.append((short_tag, line))

    # sort alphabetically
    # tags = sorted(
    #     tags,
    #     key=lambda x: x[1]
    # )

    return tags


def traverse_tag_tree(tree, inner=False):
    l = Element("ul")
    if inner:
        l.attrib["class"] = "inner-list"
        l.attrib["id"] = tree.shname
    for child in tree.children:
        e = Element("li")
        a = Element("a")
        a.attrib["href"] = URL_PREFIX + "/articlesByTag/" + child.shname
        a.text = child.fname
        e.append(a)
        l.append(e)
        if child.children:
            span = Element("span")
            span.attrib["id"] = "dropdown_" + child.shname
            span.attrib["onclick"] = "dropdown(this)"
            span.text = "  &#9660;  "
            e.append(span)
            e.append(traverse_tag_tree(child, inner=True))
    return l


def get_preview(html_text, max_symb=300):
    html_text = re.sub("<.*?>", "", html_text)
    html_text = re.sub("\s+", " ", html_text)
    html_text = unescape(html_text)
    preview = html_text[:max_symb] + "..."
    return preview


def escape_article_name(article_name: str):
    article_name = article_name.replace("/", r"%slash%")
    return article_name


def unescape_article_name(article_name: str):
    article_name = article_name.replace(r"%slash%", "/")
    return article_name
