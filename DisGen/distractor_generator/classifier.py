import pandas as pd
import numpy as np

import nltk
import re
import random

import torch as tt
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from tqdm import tqdm, tqdm_notebook
from sklearn.metrics import accuracy_score, f1_score


def calculate_accuracy_and_f1(true, pred):
    pred = pred.data.cpu()
    true = true.data.cpu()
    accuracy = accuracy_score(true, pred)
    f1 = f1_score(true, pred, average='weighted')
    return accuracy, f1

def invert_seq_batch(batch):
    ## Solution from https://discuss.pytorch.org/t/how-to-use-a-lstm-in-a-reversed-direction/14389
    inv_idx = tt.arange(batch.size(1)-1, -1, -1).long()
    return batch.index_select(1, inv_idx)


class Batch:
    def __init__(self, batch, device):
        self.left = batch.left.to(device)
        self.right = invert_seq_batch(batch.right).to(device)
        self.wrong_item = batch.wrong_item.to(device)
        self.right_item = batch.right_item.to(device)


class ErrorModel(nn.Module):
    def __init__(self, vocab_size, embed_size, hidden1_size, hidden2_size, output_size,
                 dropout1_rate=0.05, dropout2_rate=0.2, dropout3_rate=0.2, activation=nn.ReLU()):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_size)
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
        self.fc1 = nn.Linear(hidden1_size*2, hidden2_size)
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
        
        ## Concatenate:
        x = tt.cat([left,right],dim=1)
        x = self.dropout2(x)
        
        ## Apply fully connected layers:
        x = self.dropout3(self.activation(self.fc1(x)))
        x = self.fc2(x)
        return x


def train_epoch(model, train_iterator, optimizer, criterion, device, n_epoch,
                penalty_multiplier=1):
    losses = []
    model.train()
    n_batches = len(train_iterator)
    iterator = tqdm_notebook(train_iterator, total=n_batches, desc=f"Training epoch {n_epoch}", leave=True)
    
    for i, batch in enumerate(iterator):
        optimizer.zero_grad()
        
        batch = Batch(batch, device)
        pred = model(batch)
        ## Criterion should have param "reduce" set to None
        loss = criterion(pred, batch.wrong_item)
        
        if penalty_multiplier != 1:
            ## check if predicted value equals right tense:
            pen_vec = pred.argmax(dim=1) == batch.right_item
            ## form penalty vector:
            penalty_multiplier = tt.Tensor([penalty_multiplier]).to(device)
            pen_vec = pen_vec.type(tt.float).to(device)
            pen_vec = (pen_vec+1)**tt.log2(penalty_multiplier)
            ## punish if it equals:
            loss = loss * pen_vec
        loss = loss.mean()
        loss.backward()
        optimizer.step()
        
        curr_loss = loss.data.cpu().detach().item()
        iterator.set_postfix(loss=str(round(curr_loss,5)))
        acc, f1 = calculate_accuracy_and_f1(batch.wrong_item, pred.argmax(dim=1))
        losses.append((curr_loss, acc, f1))
    return np.mean(losses, axis=0)
        

def val(model, val_iterator, criterion, device, penalty_multiplier=1):
    losses =[]
    model.eval()
    n_batches = len(val_iterator)
    batch_iter = tqdm_notebook(val_iterator, total=n_batches)
    with tt.no_grad():
        for batch in batch_iter:
            batch = Batch(batch, device)
            pred = model(batch)
            loss = criterion(pred, batch.wrong_item)
            if penalty_multiplier != 1:
                ## check if predicted value equals right tense:
                pen_vec = pred.argmax(dim=1) == batch.right_item
                ## form penalty vector:
                penalty_multiplier = tt.Tensor([penalty_multiplier]).to(device)
                pen_vec = pen_vec.type(tt.float).to(device)
                pen_vec = (pen_vec+1)**tt.log2(penalty_multiplier)
                ## punish if it equals:
                loss = loss * pen_vec
            loss = loss.mean().data.cpu().detach().item()
            acc, f1 = calculate_accuracy_and_f1(batch.wrong_item, pred.argmax(dim=1))
            losses.append((loss, acc, f1))
    return np.mean(losses, axis=0)

def pred(model, val_iterator, device):
    predictions = []
    model.eval()
    n_batches = len(val_iterator)
    batch_iter = tqdm_notebook(val_iterator, total=n_batches)
    with tt.no_grad():
        for batch in batch_iter:
            batch_gpu = Batch(batch, device)
            pred = F.softmax(model(batch_gpu).data.cpu())
            predictions.append((batch.left, batch.right,
                                batch.right_item, batch.wrong_item,
                                pred))
    return predictions
    

def train(model, train_iterator, val_iterator, optimizer, criterion, device,
          scheduler, n_epochs, early_stopping=20, penalty_multiplier=1.1):
    history = pd.DataFrame()
    prev_loss = 1000
    
    for epoch in range(n_epochs):
        train_loss, train_acc, train_f1 = train_epoch(model, train_iterator, optimizer, criterion, device, epoch,
                                                     penalty_multiplier)
        print(f"Training loss: {round(train_loss,5)} accuracy: {round(train_acc,4)} f1: {round(train_f1,4)}")
        
        valid_loss, valid_acc, valid_f1 = val(model, val_iterator, criterion, device, penalty_multiplier)
        scheduler.step(valid_loss)
        
        print(f"Validation loss: {round(valid_loss,5)} accuracy: {round(valid_acc,4)} f1: {round(valid_f1,4)}")

        record = {'epoch': epoch,
                  'train_loss': train_loss, 'train_acc': train_acc, 'train_f1': train_f1,
                  'valid_loss': valid_loss, 'valid_acc': valid_acc, 'valid_f1': valid_f1}
        history = history.append(record, ignore_index=True)

        if early_stopping > 0:
            if valid_loss > prev_loss:
                es_epochs += 1
            else:
                es_epochs = 0

            if es_epochs >= early_stopping:
                best = history[history.valid_loss == history.valid_loss.min()].iloc[0]
                print(f"Early stopping! best epoch : {best['epoch']} val {best['valid_loss']} train {best['train_loss']}")
                break

            prev_loss = min(prev_loss, valid_loss)
    return history

def get_k_predicted_items(model, iterator, device, inv_labels, k=4):
    output = []
    model.eval()
    n_batches = len(iterator)
    batch_iter = tqdm_notebook(iterator, total=n_batches)
    with tt.no_grad():
        for batch in batch_iter:
            batch_gpu = Batch(batch, device)
            pred = F.softmax(model(batch_gpu).data.cpu())
            top_k = pred.topk(k=k, dim=1)
            top_probas, top_ids = top_k.values, top_k.indices
            tenses = [[inv_labels[int(i)] for i in text] for text in top_ids]
            output.append((batch.context_id, tenses, top_probas))
    return output