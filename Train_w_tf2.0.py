import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
import seaborn as sns

# Used to build and deploy machine learning apps
import tensorflow as tf

# Deep Learning API for creating Neural Networks (Runs on TensorFlow)
from tensorflow import keras 
from tensorflow.keras import layers
from tensorflow import math
from keras.utils.vis_utils import plot_model

# Scikit-learn : machine learning library
from sklearn.model_selection import train_test_split
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

# libraries for predicting
from numpy import int64
import paho.mqtt.subscribe as subscribe
import sys

import os
# Blocks GPU usage
'''os.environ["CUDA_VISIBLE_DEVICES"] = "-1"'''



############SVM, KNN, REGRESE, INDOOR POSITIONING SYSTEM - WIKI, TRIANGULACE, KALMAN FILTER + PREDNASKY, DEREK BANAS MATPLOTLIB + PANDAS , TF2.0 COURSE + PR. POZDEJI

df = pd.read_csv("NSI_WiFiProject2.0/signal_data2.csv")
'''
print(df.head())
print(X)
print(y)
print(df.shape)
print(df.describe())
print(df.isna().sum())
'''

def remove_uncommon_networks(missing_count):
    for cols in df:
        if(df[cols].isna().sum() > missing_count):
            del df[cols] # Odstranime sloupce, ktere jsou z vetsiny plne Nans hodnot

def fill_missing_val():
    for column in df:
        #df[column].fillna(df[column].min(), inplace = True) # Nahrazujeme vsechny chybejici hodnoty pomoci minim v jejich danem sloupci
        df[column].fillna(-100, inplace = True) # Nahrazujeme vsechny chybejici hodnoty jako -100

remove_uncommon_networks(485)
fill_missing_val()


X = df.drop("Room", axis = 1) # Features
y = df["Room"] # Labels


ct = make_column_transformer( # Slouzi k transformaci hodnot na jine hodnoty, v nasem pripade vsechny hodnoty normalizujeme do rozsahu 0 - 1
    (MinMaxScaler(), [col for col in df if col != 'Room']), # Normalize columns, except 'Room'
)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 66)


ct.fit(X_train) # Vypocti dulezite hodnoty pro transformaci a uloz je jako attributy transformatoru ct
X_train_normal = ct.transform(X_train)
#print(X_train_normal)
#print(X_train_normal.shape)
X_test_normal = ct.transform(X_test)
#print(ct.get_feature_names_out())


# Set random seed
tf.random.set_seed(66)

# Model1 from NN
# Dense -> vrstvy jsou plne propojene
# Activation function -> funkce, ktere slouzi k transformaci vazeneho vstupu z pripojenych predchozich neuronu na vystup
model_1 = tf.keras.Sequential([
    tf.keras.layers.Dense(8, activation=tf.keras.activations.relu), # Input layer je vyvozena z dimenze X_train, protoze neni explicitne definovana
    tf.keras.layers.Dense(8, activation=tf.keras.activations.relu),
    tf.keras.layers.Dense(8, activation=tf.keras.activations.relu),
    tf.keras.layers.Dense(5, activation = 'Softmax')
])



# optimizer -> funkce, ktera pomaha najit nejvhodnejsi vahy
# compile metoda pripravi model k trenovani (definuje optimizer, loss, metrics)
opt = tf.keras.optimizers.Adam(learning_rate = 0.03)
model_1.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(), optimizer=opt, metrics=['accuracy'])


# metoda fit trenuje model (provadi iterace na datech po dany pocet epoch)
def complex_fit():
    scheduler = tf.keras.callbacks.LearningRateScheduler(lambda epoch: 1e-4 * 10**(epoch/20))
    history = model_1.fit(X_train_normal, y_train, epochs=50, callbacks=[scheduler])
    lrs = 1e-4 * (10 ** (tf.range(50)/20))
    plt.figure(figsize=(20, 10))
    plt.semilogx(lrs, history.history['loss'])
    plt.xlabel("Learning Rate")
    plt.ylabel("Loss")
    plt.title("Learning Rate vs. Loss")
    plt.show()
#complex_fit()
history = model_1.fit(X_train_normal, y_train, epochs=70)


# Evaluate with test data
loss, acc = model_1.evaluate(X_test_normal, y_test)
print(f"Model Loss (Test Set) : {loss}")
print(f"Model Accuracy (Test Set) : {acc}")





'''
print("X_test:\n",np.array([X_test.iloc[1]]))
print("X_test specific:\n",type(np.array([X_test.iloc[1]])))
#y_prob = model_1.predict(np.array([X_test.iloc[1]]))[0]
y_prob = model_1.predict(X_test_normal)
print(y_prob)



foo = np.array([[0.0, 10.0], [0.13216, 12.11837], [0.25379, 42.05027], [0.30874, 13.11784]])

v = foo[:, 1]   # foo[:, -1] for the last column
foo[:, 1] = (v - v.min()) / (v.max() - v.min())
print(foo)


min_max_scl = MinMaxScaler()
arr = np.array([[-50, -72]]).transpose()
print(arr)
q = min_max_scl.fit_transform(arr)
print(q)

print(X_test_normal)


print(model_1.predict([[-50, -72]]))


plt.figure(figsize=(15,10))
sns.heatmap(df.corr().abs(), annot=True)
plt.show()

'''

