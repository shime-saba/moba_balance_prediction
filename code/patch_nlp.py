import pandas as pd
import numpy as np
import cPickle as pickle
import random
import re
from nltk import word_tokenize
from nltk import ngrams
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer


def add_bigrams(text_list):
    '''
    INPUT: list of strings
    OUTPUT: same list with bigrams appended to each string
    '''
    text_list_bigrams = []
    for text in text_list:
        for pair in ngrams(word_tokenize(text), 2):
            text += ' ' + ''.join(pair)
        text_list_bigrams.append(text)
    return text_list_bigrams

def process_numbers(text):
    '''
    INPUT: string
    OUTPUT: ratio between means of first two "groups" of numbers found in string
    groups are identified as runs of numbers or percents separated by / or ->

    For example, the output of "damage increased from 5/10/15/20 to 10/20/30/40"
    would be (10+20+30+40)/(5+10+15+20) = 2

    The regex is maybe too specific to observed cases, and errs on the side of
    catching too much, but it performs well enough.
    '''
    numbers = re.findall(r'([\d\-][\d\/\.%\->x]*\s.{2,13}\s[\d\/\.%\->x]+)', text)
    if len(numbers) > 0:
        output = numbers[0]
        numbers = numbers[0].replace('->', '/').replace('%', '').replace('x', '').split()
        if '-' in numbers[0]:
            numbers[0] = numbers[0].replace('-', '')
            numbers[-1] = numbers[-1].replace('-', '')
        start_vals = np.array(numbers[0].strip('.').split('/')).astype(float)
        end_vals = np.array(numbers[-1].strip('.').split('/')).astype(float)
        eps = 0.000001
        ratio = (end_vals.mean()+eps) / (start_vals.mean()+eps)
        return round(ratio, 3)
    else:
        return None

def add_ratios(text_list):
    '''
    helper function for get_info_from_df.
    INPUT: list of strings
    OUTPUT: Two-
    (1) list of strings with "increased" or "reduced" added in before
    first instance of the word "from" according to ratio between numbers found
    in the string. If no numerical change is found, the string is untouched.
    (2) list of ratios found in each string, for use in later feature
    engineering.
    '''
    ratios = []
    text_list_ratios = []
    for text in text_list:
        ratio = process_numbers(text)
        ratios.append(ratio)
        if ratio:
            text_split = text.split('from', 1)
            if ratio > 1:
                if 'rescaled' in text:
                    text = text.replace('rescaled', 'increased')
                elif 'increased' not in text:
                    if len(text_split) > 1:
                        text = text_split[0] + 'increased from' + text_split[1]
                    else:
                        text += ' increased'
            elif ratio < 1:
                if 'rescaled' in text:
                    text = text.replace('rescaled', 'reduced')
                elif 'reduced' not in text:
                    if len(text_split) > 1:
                        text = text_split[0] + 'reduced from' + text_split[1]
                    else:
                        text += ' reduced'
        text_list_ratios.append(text)
    return text_list_ratios, ratios


def get_info_from_df(df, labeled=False, check_ratios=True, nostops=True, snowball=True, bigrams=True):
    '''
    INPUT: DataFrame, boolean for presence of change_type labels,
           several optional parameters for text processing
    OUTPUT: text processed according to specified parameters,
            change_type labels (if specified), list of ratios (see above)
    '''
    change_texts = []
    labels = []
    ratios = []
    for i, row in df.iterrows():
        for j, text in enumerate(row['text_no_abi']):
            change_texts.append(text.lower().replace('\n', ''))
            if labeled:
                labels.append(row['change_type'][j])

    if check_ratios:
        change_texts, ratios = add_ratios(change_texts)
    if nostops:
        stops = set(stopwords.words('english'))
        change_texts = [' '.join([word for word in text.split(' ') if word not in stops]) for text in change_texts]
    if snowball:
        snowball = SnowballStemmer('english')
        change_texts = [' '.join([snowball.stem(word) for word in text.split(' ')]) for text in change_texts]
    if bigrams:
        change_texts = add_bigrams(change_texts)

    if labeled:
        return change_texts, ratios, labels
    else:
        return change_texts, ratios

def kFold_TFIDF_CV(text_data, labels, model, n_folds=3, use_idf=True, shuffle_seed=None, **params):
    '''
    INPUT: list of strings, labels, ML model to fit, additional optional parameters
    OUTPUT: dictionary with accuracy and auc scores for the given model

    the purpose of this function is to perform kfold cross-validation of TFIDF
    data without contaminating the TFIDF matrices with test/holdout data.
    '''
    text_label_zip = zip(text_data, labels)
    if shuffle_seed:
        random.seed(shuffle_seed)
    random.shuffle(text_label_zip)
    text_shuffled = np.array([row[0] for row in text_label_zip])
    labels_shuffled = np.array([row[1] for row in text_label_zip])
    cutoffs = [i * int(len(text_data)/float(n_folds)) for i in xrange(n_folds)] + [len(text_data)]

    all_acc = []
    all_auc = []
    for i, start_pt in enumerate(cutoffs[:-1]):
        end_pt = cutoffs[i+1]
        holdout_text = text_shuffled[start_pt:end_pt]
        holdout_labels = labels_shuffled[start_pt:end_pt]
        train_text = np.concatenate((text_shuffled[:start_pt], text_shuffled[end_pt:]))
        train_labels = np.concatenate((labels_shuffled[:start_pt], labels_shuffled[end_pt:]))

        tfidf_train = TfidfVectorizer(use_idf=use_idf)
        tfmat_train = tfidf_train.fit_transform(train_text)
        tfmat_test = tfidf_train.transform(holdout_text)

        model.set_params(**params)
        model.fit(tfmat_train.toarray(), train_labels)
        all_acc.append(model.score(tfmat_test.toarray(), holdout_labels))
        all_auc.append(roc_auc_score(holdout_labels, model.predict_proba(tfmat_test.toarray())[:, 1]))

    return {'acc': np.mean(all_acc), 'auc': np.mean(all_auc)}
