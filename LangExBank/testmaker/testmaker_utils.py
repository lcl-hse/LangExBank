import os, json, re

meta_fields = [
    'text_type',
    'ielts',
    'CEFR_level',
    'task_id',
    'ann_checked',
    'work_type',
    'task_id'
]

def empty_meta():
    meta = {key:None for key in meta_fields}
    meta['filename'] = None
    meta['folder'] = None
    return meta

def load_meta(file_name):
    meta = dict()
    try:
        with open(file_name+'.json', 'r', encoding='utf-8') as inp:
            json_dict = json.load(inp)
        assert type(json_dict) == dict
        for key in meta_fields:
            if key in json_dict:
                meta[key] = json_dict[key]
            else:
                meta[key] = None
    except (FileNotFoundError, AssertionError, json.JSONDecodeError):
        meta = {key:None for key in meta_fields}
    splitter = file_name.rfind('/')
    meta['filename'] = file_name[splitter+1:]
    meta['folder'] = file_name[:splitter]
    return meta

def save_meta(meta, file_name):
    with open(file_name, 'w', encoding='utf-8') as outp:
        json.dump(meta, outp, ensure_ascii=False)

class ProcessedText(object):
    def __init__(self, text, meta):
        self.text = text
        self.meta = meta

class ProcessedTextFileIter(object):
    def __init__(self, path):
        self.path = path
        self.file_list = [f for f in os.listdir(self.path) if f.endswith('.txt')]
    
    def __iter__(self):
        self._list_pointer = 0
        return self
    
    def __next__(self):
        if self._list_pointer < len(self.file_list):
            text_fname = self.path + self.file_list[self._list_pointer]

            meta_fname = text_fname[:-4]+'.json'
            try:
                with open(text_fname, 'r', encoding='utf-8') as inp:
                    text = inp.read()
                with open(meta_fname, 'r', encoding='utf-8') as inp:
                    meta = json.load(inp)
            except UnicodeDecodeError:
                meta = empty_meta()
            ptext = ProcessedText(text, meta)
            self._list_pointer += 1
            return ptext
        else:
            raise StopIteration
    
    def __len__(self):
        return len(self.file_list)