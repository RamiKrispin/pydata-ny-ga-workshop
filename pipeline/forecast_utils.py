import pandas as pd
from statistics import mean
from mlforecast import MLForecast
from mlforecast.target_transforms import Differences
from mlforecast.utils import PredictionIntervals
from window_ops.expanding import expanding_mean
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression


def models_reformat(models):
    for i in range(len(models)):
        if isinstance(models[i], str):
            models[i] = eval(models[i])

def fc_to_long(fc, models, level):
    f = None
    models_reformat(models = models)
    for m in models:      
        m_name = type(m).__name__
        temp = fc[["unique_id","ds"]]
        temp["forecast"] = fc[m_name] 
        temp["lower"] = fc[m_name + "-lo-" + str(level)]
        temp["upper"] = fc[m_name + "-hi-" + str(level)]
        temp["model"] = m_name
        if f is None:
            f = temp
        else:
            f = pd.concat([f, temp])

    return f

def mape(y, yhat):
    mape = mean(abs(y - yhat)/ y) 
    return mape

def rmse(y, yhat):
    rmse = (mean((y - yhat) ** 2 )) ** 0.5
    return rmse

def coverage(y, lower, upper):
    coverage = sum((y <= upper) & (y >= lower)) / len(y)
    return coverage