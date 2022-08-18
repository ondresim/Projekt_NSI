import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction import DictVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline

# Scikit-learn : machine learning library
from sklearn.model_selection import train_test_split
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

# libraries for predicting
from numpy import int64
import paho.mqtt.subscribe as subscribe
import sys

from sklearn import metrics

import os
# Blocks GPU usage
'''os.environ["CUDA_VISIBLE_DEVICES"] = "-1"'''


df = pd.read_csv("NSI_WiFiProject2.0/signal_data2.csv")
print("DataFrame shape:",df.shape)


def remove_uncommon_networks(missing_count):
    for cols in df:
        if(df[cols].isna().sum() > missing_count):
            del df[cols] # Odstranime sloupce, ktere jsou z vetsiny plne NaN hodnot


def fill_missing_val():
    for column in df:
        df[column].fillna(-100, inplace = True)


#remove_uncommon_networks(490)
fill_missing_val()


X = df.drop("Room", axis = 1) # Features
y = df["Room"] # Labels
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 66)


import pickle # Never unpickle untrusted data as it could lead to malicious code being executed upon loading.


def support_vector_machine():
    clf = SVC(kernel='linear')
    clf.fit(X_train, np.ravel(y_train))
    y_pred = clf.predict(X_test)
    print("Accuracy:",metrics.accuracy_score(y_test, y_pred))
    return clf


def KNN():
    neigh = KNeighborsClassifier(n_neighbors=3)
    neigh.fit(X_train, y_train)
    y_pred = neigh.predict(X_test)
    print("Accuracy:",metrics.accuracy_score(y_test, y_pred))
    return neigh


def random_forest():
    rf = RandomForestClassifier(n_estimators = 100) 
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    print("Accuracy:",metrics.accuracy_score(y_test, y_pred))
    return rf


# DictVectorizer converts list of dictionaries to 2D array
# Kazdy sloupec s ciselnymi hodnotami tvori 1 Feature, sloupce se stringy jako hodnotami tvori tolik features, kolik je ruznych hodnot prirazenych ke klicum
def dic_vectorizer():
    rf = RandomForestClassifier(n_estimators = 100) 
    pipe = make_pipeline(DictVectorizer(sparse=False), rf)
    X2 = df.drop("Room", axis = 1).to_dict(orient = 'records') # List slovniku
    y2 = df['Room'].values

    arr = []
    for dic in X2:
        dic = {key: dic[key] for key in dic if (dic[key] != -100)} #Novy list slovniku bez NaN hodnot (odstranujeme hodnoty doplnene jako -100)
        #back_to_dict[i] = {k: i[k] for k in i if not isnan(i[k])}
        arr.append(dic)

    #print(arr)
    #print(X2)

    X2_train, X2_test, y2_train, y2_test = train_test_split(arr, y2, test_size = 0.2, random_state = 66)

    pipe.fit(X2_train, y2_train)
    print("Pipeline feature names:",pipe[:-1].get_feature_names_out())
    print("Pipeline score:",pipe.score(X2_test, y2_test))


dic_vectorizer()
model = random_forest()
with open('NSI_WiFiProject2.0/Model_library/rf_model2.pkl','wb') as f:
        pickle.dump(model,f)



plt.figure(figsize=(15,10))
sns.heatmap(df.corr().abs(), annot=True)
plt.show()

