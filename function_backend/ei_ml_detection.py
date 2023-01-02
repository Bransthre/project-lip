from . import ei_database as ei_ds
from . import ei_decision_tree as ei_dt
import random as random
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, top_k_accuracy_score
from sklearn.preprocessing import OneHotEncoder
np.seterr(all="ignore")

ALL_EMOS = ["neutral", "positive", "negative"]

def prepare_dataset(target_class, data = None):
    if data is None:
        model_dataset = ei_ds.get_sample_data(target_class = target_class)
        model_dataset = ei_dt.increase_database_variance(model_dataset, 3)
    else:
        model_dataset = data
    if "log_loc" in model_dataset.columns:
        locations = model_dataset["log_loc"]
        locations = pd.concat(
            [locations, pd.Series(["Study Space", "Home", "Workplace", "Eatery"])]
        )
        locations = pd.get_dummies(
            locations, prefix = "log_loc", drop_first = False
        )[:-4]
        model_dataset = pd.merge(model_dataset.drop("log_loc", axis = 1), locations, left_index = True, right_index = True)
    return model_dataset

def train_model(target_class, verbose = False, train_ratio = 0.8):
    if verbose:
        print("=" * 20)
    model_dataset = prepare_dataset(target_class)
    model = RandomForestClassifier(
        class_weight = "balanced_subsample",
        n_estimators = 300,
        random_state = 10
    )
    training_set, test_set = train_test_split(
        model_dataset,
        test_size = 0.2,
        random_state = 10
    )
    X_train, Y_train = training_set.drop(target_class, axis = 1), training_set[target_class]
    X_test, Y_test = test_set.drop(target_class, axis = 1), test_set[target_class]
    model.fit(X_train, Y_train)
    if verbose:
        model_response = model.predict(X_train)
        accuracy = accuracy_score(
            Y_train,
            model_response
        )
        print(
            f"Training accuracy of model is {accuracy}"
        )
        model_response = model.predict(X_test)
        accuracy = accuracy_score(
            Y_test,
            model_response
        )
        print(
            f"Testing accuracy of model is {accuracy}"
        )
    return model

