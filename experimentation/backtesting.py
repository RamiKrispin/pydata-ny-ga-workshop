import pandas as pd
import datetime
import mlflow
from statistics import mean
from mlforecast import MLForecast
from mlforecast.target_transforms import Differences
from mlforecast.utils import PredictionIntervals
from window_ops.expanding import expanding_mean
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor





def check_experiment(experiment_name, verbose = True):
    class experiment_check:
        def __init__(output, experiment_name, experiment_meta, experiment_exists):
            output.experiment_name = experiment_name
            output.experiment_meta = experiment_meta
            output.experiment_exists = experiment_exists
            
    ex = mlflow.get_experiment_by_name(experiment_name)
    exists_flag = None
    if ex is None:
        if(verbose):
            print("Experiment " + experiment_name + " does not exist")
        exists_flag = False
        ex_meta = None
    else:

        if(verbose):
            print("Experiment " + experiment_name +  " exists")
        exists_flag = True
        ex_meta = dict(ex)

    output = experiment_check(experiment_name = experiment_name, 
                                experiment_meta = ex_meta,
                                experiment_exists = exists_flag)
    return output 



def start_experiment(experiment_name, mlflow_path, tags, verbose = True):
    meta = None
    try:
        mlflow.create_experiment(name = experiment_name,
                                artifact_location= mlflow_path,
                                tags = tags)
        meta = mlflow.get_experiment_by_name(experiment_name)
        if verbose:
            print(f"Set a new experiment {experiment_name}")
            print("Pulling the metadata")
    except:
        if verbose:
            print(f"Experiment {experiment_name} exists, pulling the metadata")
        meta = mlflow.get_experiment_by_name(experiment_name)

    return meta


def mlflow_log(obj, mlflow_path, verbose = True):
    run_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    runs_meta = None

    for i in obj.score["unique_id"].unique():
        tags = {
            "type": "backtesting",
            "unique_id": i,
            "time": run_time
        }

        exp_check = check_experiment(experiment_name = i)
        exp_meta = start_experiment(experiment_name = exp_check.experiment_name, 
                                        mlflow_path = mlflow_path, 
                                        tags = tags)

        run_name = i + "_" + run_time

        df = obj.score[obj.score["unique_id"] == i]

        for m in df["model_unique_id"].unique():
            d = df[df["model_unique_id"] == m]
            if verbose:
                print("Logging model:",i, m)
            model = d["model"].unique()[0]
            label = d["label"].unique()[0]

            model_params = obj.models[label]["args"]
            model_params["models"] = model
            model_params["type"] =  obj.models[label]["type"]
            model_params["model_unique_id"] = m
            model_params["n_windows"] = obj.settings["n_windows"]
            model_params["h"] = obj.settings["h"]
            model_params["prediction_intervals_method"] = obj.settings["prediction_intervals"]["method"]
            model_params["prediction_intervals_h"] = obj.settings["prediction_intervals"]["h"]
            model_params["prediction_intervals_level"] = obj.settings["prediction_intervals"]["level"]

            for index, row in d.iterrows():
                with mlflow.start_run(experiment_id = exp_meta.experiment_id, 
                run_name = run_name,
                tags = {"type": "backtesting",
                "partition": row["partition"], 
                "unique_id": row["unique_id"],
                "model_unique_id": m,
                "model": model,
                "run_name": run_name,
                "label": label}) as run:
                    mlflow.log_params(model_params)
                    mlflow.log_metric("mape", row["mape"])
                    mlflow.log_metric("rmse", row["rmse"])
                    mlflow.log_metric("coverage", row["coverage"])
                    runs_temp = row.to_frame().T
                    runs_temp["run_name"] = run_name
                    runs_temp["experiment_id"] = exp_meta.experiment_id

                    if runs_meta is None:
                        runs_meta = runs_temp
                    else:
                        runs_meta = pd.concat([runs_meta, runs_temp])
        mlflow.end_run()
    return runs_meta


class backtesting:
    def __init__(self):
        pass

    def add_input(self,input):
        self.input = input

    def add_settings(self, models, settings):
        self.models = models
        self.settings = settings

    def run_backtesting(self):
        check = all([l in  self.__dict__.keys() for l in ["input", "models", "settings"]])
        if not check:
            print("Error: some arguments are missings")
            return         
        # experiment_id = mlflow.create_experiment(self.experiment_name)

        output = train_backtesting(input = self.input,
                                models = self.models, 
                                settings = self.settings)
        self.results = output.backtesting

        score = bkt_score(bkt = output.backtesting)

        self.top = score.top
        self.leaderboard = score.leaderboard
        self.score = score.score
    
    def log_backtesting(self, mlflow_path, verbose):
        check = all([l in  self.__dict__.keys() for l in ["input", "models", "settings", "score"]])
        if not check:
            print("Error: some arguments are missings")
            return 
        score = None
        score = mlflow_log(obj = self, mlflow_path = mlflow_path, verbose = verbose)

        if score is not None:
            self.score = score
        else:
            print("Could not log the backtesting metadata to mlflow")






def models_reformat(models):
    for i in range(len(models)):
        if isinstance(models[i], str):
            models[i] = eval(models[i])


def mape(y, yhat):
    mape = mean(abs(y - yhat)/ y) 
    return mape

def rmse(y, yhat):
    rmse = (mean((y - yhat) ** 2 )) ** 0.5
    return rmse

def coverage(y, lower, upper):
    coverage = sum((y <= upper) & (y >= lower)) / len(y)
    return coverage

def bkt_to_long(bkt, models, level):
    f = None
    
    models_reformat(models = models)
    for m in models:      
        m_name = type(m).__name__
        temp = bkt[["unique_id","ds", "y", "cutoff"]].copy()
        temp["forecast"] = bkt[m_name] 
        temp["lower"] = bkt[m_name + "-lo-" + str(level)]
        temp["upper"] = bkt[m_name + "-hi-" + str(level)]
        temp["model"] = m_name
        if f is None:
            f = temp
        else:
            f = pd.concat([f, temp])

    cutoff = f["cutoff"].unique()
    partitions_mapping  = pd.DataFrame({"cutoff": cutoff})
    partitions_mapping["partition"] = range(1, len(cutoff) + 1)
    f = f.merge(right = partitions_mapping, left_on = "cutoff", right_on = "cutoff")

    return f


def backtesting_ml(input, model_args, settings):
    args = model_args.copy()
    models_list = args["models"].copy()
    models_reformat(models = models_list)
    if "lags" not in args.keys():
        args["lags"] = None
    if "date_features" not in args.keys():
        args["date_features"] = None
    if "target_transforms" not in args.keys():
        args["target_transforms"] = None

    mlf = MLForecast(
        models=models_list, 
        freq= args["freq"],
        date_features = args["date_features"],
        target_transforms= args["target_transforms"],
        lags = args["lags"])

    bkt = mlf.cross_validation(
        df=input,
        h=settings["h"],
        n_windows=settings["n_windows"],
        prediction_intervals = PredictionIntervals(n_windows=settings["prediction_intervals"]["n_windows"], 
        h = settings["prediction_intervals"]["h"], 
        method = settings["prediction_intervals"]["method"]),
        level = [settings["prediction_intervals"]["level"]])

    bkt_long = bkt_to_long(bkt = bkt, 
    models = models_list , 
    level = settings["prediction_intervals"]["level"])

    return bkt_long

def train_backtesting(input, models, settings):
    
    class backtesting:
        def __init__(self, models, settings, backtesting):
            self.models = models  
            self.settings = settings
            self.backtesting = backtesting
    
    bkt_df = None
    for m in models.keys():
        if models[m]["type"] == "mlforecast":
            args = models[m]["args"]
            bkt_temp = backtesting_ml(input, model_args = args, settings = settings)
            bkt_temp["label"] = m
            bkt_temp["type"] = "mlforecast"
            if bkt_df is None:
                bkt_df = bkt_temp
            else:
                bkt_df = pd.concat([bkt_df, bkt_temp])

    output = backtesting(models = models, settings = settings, backtesting = bkt_df)

    return output

def bkt_score(bkt):
    class backtesting_score:
        def __init__(self, score, leaderboard, top):
            self.score = score  
            self.leaderboard = leaderboard
            self.top = top


    score_df = None
    for u in bkt["unique_id"].unique():
        for l in bkt["label"].unique():
            for p in bkt["partition"].unique():
                bkt_sub = bkt[(bkt["unique_id"] == u) & (bkt["label"] == l) & (bkt["partition"] == p)]
                for m in bkt_sub["model"].unique():
                    bkt_model = bkt_sub[bkt_sub["model"] == m]
                    mape_score = mape(y = bkt_model["y"], yhat = bkt_model["forecast"]) 
                    rmse_score = rmse(y = bkt_model["y"], yhat = bkt_model["forecast"]) 
                    coverage_score = coverage(y = bkt_model["y"], lower = bkt_model["lower"], upper = bkt_model["upper"]) 
                    score_temp = {
                        "unique_id": u,
                        "label": l,
                        "type": bkt_model["type"].unique()[0],
                        "partition": p,
                        "model": m,
                        "mape": mape_score,
                        "rmse": rmse_score,
                        "coverage": coverage_score
                    }

                    if score_df is None:
                        score_df = pd.DataFrame([score_temp])
                    else:
                        score_df = pd.concat([score_df, pd.DataFrame([score_temp])])
    score_df["model_unique_id"] = score_df["label"] + "_" +score_df["model"]
    score_df.reset_index(drop=True, inplace=True)
    leaderboard_df = bkt_leaderboard(score = score_df)
    top_df = top_models(leaderboard = leaderboard_df)

    output = backtesting_score(score = score_df, 
                            leaderboard = leaderboard_df,
                            top = top_df)
    
    return output


def bkt_leaderboard(score):
    leaderboard = None
    for i in score["unique_id"].unique():
        for m in score["model_unique_id"].unique():
            l = score[(score["model_unique_id"] == m) & (score["unique_id"] == i)]

            mape = mean(l["mape"])
            rmse = mean(l["rmse"])
            coverage = mean(l["coverage"])

            temp = {
                "model_unique_id": m,
                "unique_id": i,
                "label": l["label"].unique()[0],
                "model": l["model"].unique()[0],
                "type": l["type"].unique()[0],
                "partitions": l["partition"].max(),
                "avg_mape": mape,
                "avg_rmse": rmse,
                "avg_coverage": coverage
            }

            if leaderboard is None:
                leaderboard = pd.DataFrame([temp])
            else:
                leaderboard = pd.concat([leaderboard, pd.DataFrame([temp])])
    leaderboard.reset_index(drop=True, inplace=True)
    return leaderboard


def top_models(leaderboard, metric = "mape"):
    top = None
    for i in leaderboard["unique_id"].unique():
        l = leaderboard[leaderboard["unique_id"] == i]
        if metric in ["mape", "rmse"]:
            l_top = l[l["avg_" + metric] == l["avg_" + metric].min()]
        elif metric == "coverage":
            l_top =  l[l["avg_" + metric] == l["avg_" + metric].max()]
        if top is None:
            top = l_top
        else:
            top = pd.concat([top, l_top])
    top.reset_index(drop=True, inplace=True)
    return top