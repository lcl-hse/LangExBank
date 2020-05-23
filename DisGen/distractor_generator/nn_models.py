import torch as tt
import torch.nn as nn
import torch.nn.functional as F

import json, os

from torchtext.data import Field, LabelField, BucketIterator, Dataset, Example, RawField
from torchtext.vocab import Vocab

from collections import Counter

def load_vocab(dir_name):
  freqs_path = os.path.join(dir_name, 'freqs.json')
  itos_path = os.path.join(dir_name, 'itos.json')
  stoi_path = os.path.join(dir_name, 'stoi.json')

  with open(freqs_path, 'r', encoding='utf-8') as finp:
    freqs = Counter(json.load(finp))
  with open(itos_path, 'r', encoding='utf-8') as finp:
    itos = json.load(finp)
  with open(stoi_path, 'r', encoding='utf-8') as finp:
    stoi = json.load(finp)
  
  vocab = Vocab(freqs)
  vocab.itos = itos
  vocab.stoi = stoi

  return vocab

def invert_seq_batch(batch):
    ## Solution from https://discuss.pytorch.org/t/how-to-use-a-lstm-in-a-reversed-direction/14389
    inv_idx = tt.arange(batch.size(1)-1, -1, -1).long()
    return batch.index_select(1, inv_idx)

## Taken from https://gist.github.com/nissan/ccb0553edb6abafd20c3dec34ee8099d with modification
class DataFrameDataset(Dataset):
    def __init__(self, df, question_field, answer_field, right_answer_col):
        # print(right_answer_col)
        # df.to_excel("Test.xlsx")
        fields = [('context_id', RawField()), ('left', question_field), ('right', question_field), ('right_item', answer_field)]
        examples = []
        for i, row in df.iterrows():
            left = row.left
            right = row.right
            right_answer = row[right_answer_col]
            # if right_answer not in answer_field.vocab.stoi:
            #   print(right_answer)
            examples.append(Example.fromlist([i, left, right, right_answer], fields))

        super().__init__(examples, fields)


class Batch:
    def __init__(self, batch, device):
        self.left = batch.left.to(device)
        self.right = invert_seq_batch(batch.right).to(device)
        self.right_item = batch.right_item.to(device)


class W2VErrorModel(nn.Module):
    def __init__(self, vocab_size, embed_size, hidden1_size, hidden2_size, output_size,
                 dropout1_rate=0.05, dropout2_rate=0.1, dropout3_rate=0.2, activation=nn.ReLU()):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_size)
        self.frozen_embedding = nn.Embedding(output_size, embed_size)
        
        self.dropout1 = nn.Dropout(p=dropout1_rate)
        
        self.lstm1 = nn.LSTM(input_size=embed_size,
                             hidden_size=hidden1_size,
                             batch_first=False,
                             bidirectional=False)
        self.lstm2 = nn.LSTM(input_size=embed_size,
                             hidden_size=hidden1_size,
                             batch_first=False,
                             bidirectional=False)
        
        self.dropout2 = nn.Dropout(p=dropout2_rate)
        self.fc1 = nn.Linear(hidden1_size*2+embed_size, hidden2_size)
        self.activation = activation
        self.dropout3 = nn.Dropout(p=dropout3_rate)
        self.fc2 = nn.Linear(hidden2_size, output_size)
    
    def forward(self, batch):
        ## Run forward-LSTM on left context of error:
        left = self.embedding(batch.left)
        left = self.dropout1(left)
        left, _ = self.lstm1(left)
        left = left[-1]
        
        ## Run backward-LSTM on Left context of error:
        right = self.embedding(batch.right)
        right = self.dropout1(right)
        right, _ = self.lstm2(right)
        right = right[-1]
        
        correction = self.frozen_embedding(batch.right_item)
        
        ## Concatenate:
        x = tt.cat([left,right,correction],dim=1)
        x = self.dropout2(x)
        
        ## Apply fully connected layers:
        x = self.dropout3(self.activation(self.fc1(x)))
        x = self.fc2(x)
        return x

def get_k_predicted_items(model, batch_iter, device, inv_labels, k=4):
    output = []
    model.eval()
    with tt.no_grad():
        for batch in batch_iter:
            batch_device = Batch(batch, device)
            pred = F.softmax(model(batch_device).data.cpu())
            top_k = pred.topk(k=k, dim=1)
            top_probas, top_ids = top_k.values, top_k.indices
            items = [[inv_labels[int(i)] for i in text] for text in top_ids]
            output.append((batch.context_id, items, top_probas))
    return output