import os
from pandas import DataFrame, Series
from sklearn.externals import joblib
from sklearn.ensemble import GradientBoostingClassifier

gbm_tuned = joblib.load('fpd_gbm.pkl')
def predict(features):
    return gbm_tuned.predict_proba(DataFrame(features))[:,1][0]
