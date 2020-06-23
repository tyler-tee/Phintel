import math
import numpy as np
import pandas as pd
import random
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


def get_tokens(urls):
    tokens_by_slash = str(urls.encode('utf-8')).split('/')  # get tokens after splitting by slash
    all_tokens = []
    for i in tokens_by_slash:
        tokens = str(i).split('-')  # get tokens after splitting by dash
        tokens_by_dot = []
        for j in range(0, len(tokens)):
            temp_tokens = str(tokens[j]).split('.')  # get tokens after splitting by dot
            tokens_by_dot = tokens_by_dot + temp_tokens
        all_tokens = all_tokens + tokens + tokens_by_dot
    all_tokens = list(set(all_tokens))  # remove redundant tokens
    if 'com' in all_tokens:
        all_tokens.remove(
            'com')  # removing .com since it occurs a lot of times and it should not be included in our features
    return all_tokens


def TL():
    df_allurls = pd.read_csv('dataset.csv', dtype={'url': str, 'category': str},
                             error_bad_lines=False)  # reading file

    allurlsdata = np.array(df_allurls)  # converting it into an array
    random.shuffle(allurlsdata)  # shuffling

    categories = [d[1] for d in allurlsdata]  # all labels
    corpus = [str(d[0]) for d in allurlsdata]  # all urls corresponding to a label (either good or bad)
    vectorizer = TfidfVectorizer(tokenizer=get_tokens)  # get a vector for each url but use our customized tokenizer
    x_vector = vectorizer.fit_transform(corpus)  # get the X vector

    x_train, x_test, y_train, y_test = train_test_split(x_vector, categories, test_size=0.2,
                                                        random_state=42)  # split into training and testing set 80/20

    lgs = LogisticRegression()  # using logistic regression
    lgs.fit(x_train, y_train)
    print(lgs.score(x_test, y_test))
    return vectorizer, lgs


"""
vectorizer, lgs = TL()

x_predict = ['wikipedia.com']

x_predict = vectorizer.transform(x_predict)

y_predict = lgs.predict(x_predict)

print(y_predict)
"""
