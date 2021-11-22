import datetime
from typing import List
import numpy as np
import pandas as pd
import pickle
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


model_loaded = False


def get_tokens(url: str) -> List:
    tokens = list(set(re.split('[/.-?=]', url)))  # Split our URL on any of these delimiters

    tokens = [token for token in tokens if token and token != 'com']

    return tokens


# Used ml_dataset.csv for the below f(x) to achieve a 97-98% score
def predict_train(dataset: str):
    df_allurls = pd.read_csv(dataset, dtype={'url': str, 'label': str},
                             error_bad_lines=False)  # reading file

    allurlsdata = np.array(df_allurls)  # Convert the dataframe to an array
    random.shuffle(allurlsdata)  # Shuffle the produced array

    categories = [d[1] for d in allurlsdata]  # all labels
    corpus = [str(d[0]) for d in allurlsdata]  # all urls corresponding to a label (either good or bad)

    vectorizer = TfidfVectorizer(tokenizer=get_tokens, use_idf=True, smooth_idf=True,
                                 sublinear_tf=False)  # get a vector for each url but use our customized tokenizer
    x_vector = vectorizer.fit_transform(corpus)  # get the X vector

    model = LogisticRegression(random_state=0)

    x_train, x_test, y_train, y_test, indices_train, indices_test = train_test_split(x_vector, categories,
                                                                                     df_allurls.index, test_size=0.2,
                                                                                     random_state=0)
    model.fit(x_train, y_train)

    clf = LogisticRegression(random_state=0)
    clf.fit(x_train, y_train)
    train_score = clf.score(x_train, y_train)
    test_score = clf.score(x_test, y_test)

    return vectorizer, clf, train_score, test_score


def save_predict(model: pickle, vectorizer: pickle):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H%M')

    with open(f'ml_model {timestamp}.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open(f'ml_vectorizer {timestamp}.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)


def load_trained(model_pkl: str, vectorizer_pkl: str):
    with open(model_pkl, 'rb') as f:
        model = pickle.load(f)
    with open(vectorizer_pkl, 'rb') as f:
        vectorizer = pickle.load(f)

    return model, vectorizer


def url_predict(url_lst, vectorizer, model):
    x_predict = vectorizer.transform(url_lst)
    y_predict = model.predict(x_predict)

    return y_predict
