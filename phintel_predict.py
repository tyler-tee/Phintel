import numpy as np
import pandas as pd
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


def get_tokens(urls):
    tokens = list(set(re.split('[/.-]', urls)))

    tokens = [token for token in tokens if token and token != 'com']

    return tokens


def TL():
    df_allurls = pd.read_csv('dataset.csv', dtype={'url': str, 'category': str},
                             error_bad_lines=False)  # reading file

    allurlsdata = np.array(df_allurls)  # converting it into an array
    print(allurlsdata)

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

x_predict = ['google.com']

x_predict = vectorizer.transform(x_predict)

y_predict = lgs.predict(x_predict)

print(y_predict)
"""
