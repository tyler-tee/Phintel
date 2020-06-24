import numpy as np
import pandas as pd
import pickle
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


def get_tokens(urls):
    tokens = list(set(re.split('[/.-?=]', urls)))

    tokens = [token for token in tokens if token and token != 'com']

    return tokens


def TL():
    df_allurls = pd.read_csv('ml_dataset.csv', dtype={'url': str, 'label': str},
                             error_bad_lines=False)  # reading file

    allurlsdata = np.array(df_allurls)  # converting it into an array

    random.shuffle(allurlsdata)  # shuffling

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
    print(train_score)
    print(test_score)

    return vectorizer, clf


vectorizer, lgs = TL()


def save_model():
    with open('ml_model.pkl', 'wb') as f:
        pickle.dump(lgs, f)
    with open('ml_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)


save_model()


x_predict = ['sportsauthority.com', 'russiansite.ru/virus.exe', 'wikipedia.com']

x_predict = vectorizer.transform(x_predict)

y_predict = lgs.predict(x_predict)

print(y_predict)
