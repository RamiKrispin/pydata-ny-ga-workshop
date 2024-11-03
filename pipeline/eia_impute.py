import numpy as np
import pandas as pd

def impute_missing(input, var, index):
    class imputed_values:
        def __init__(self, data, missing_index, num_imputed):
            self.data = data
            self.missing_index = missing_index
            self.num_imputed = num_imputed
    df = input.copy()
    df.loc[:,"impute"] = np.NaN
    df = df.sort_values(by = [index])
    missing_index = df[df[var].isnull()].index.tolist()
    non_missing_index = df.index.difference(missing_index).tolist()
    num_imputed = 0
    for i in missing_index:
        if i > 336:
            df.loc[i ,"impute"] = (df.loc[i - 336 ,var] + df.loc[i - 168 ,var] + df.loc[i - 24 ,var]) / 3
            num_imputed = num_imputed + 1
        elif i > 168:
            df.loc[i ,"impute"] = (df.loc[i - 168 ,var] + df.loc[i - 24 ,var]) / 2
            num_imputed = num_imputed + 1
        elif i > 24:
            df.loc[i ,"impute"] = df.loc[i - 24 ,var]
            num_imputed = num_imputed + 1
        else:
            print("There are not enough observations to impute observation:", i)
        df["y"] = np.NaN

    df.loc[missing_index, "y"] = df.loc[missing_index, "impute"]
    df.loc[non_missing_index, "y"] = df.loc[non_missing_index, var]
    output = imputed_values(data = df, missing_index = missing_index, num_imputed = num_imputed)
    return output



def impute_series(series, metadata):
    class imputed_series:
        def __init__(self, data, metadata):
            self.data = data
            self.metadata = metadata
    ts = series.copy()
    meta = metadata.copy()
    new_df = None
    for index, row in meta.iterrows():
        s = row["subba"]
        temp = None
        temp = ts[ts["subba"] == s]
        if row["na"] > 0:
            print("Series", s, "has", row["na"], "missing values")
            imputed = impute_missing(input = temp, var = "value", index = "period")
            if imputed.num_imputed > 0:
                temp = imputed.data
                meta.loc[index, "imputed"] = imputed.num_imputed
                meta.loc[index, "comments"] = meta.loc[index, "comments"] + " Missing values were imputed"
            else:
                temp["impute"] = np.NaN
                temp["y"] = temp["value"]
        else:
            temp["impute"] = np.NaN
            temp["y"] = temp["value"]
        if all([meta.loc[index, "na"] == meta.loc[index, "imputed"],meta.loc[index, "start_match"],meta.loc[index, "end_match"]]):
            meta.loc[index, "success"] = True
            meta.loc[index, "update"] = True
        if meta.loc[index, "success"]:
            if new_df is None:
                new_df = temp
            else:
                new_df = pd.concat([new_df, temp])
    if new_df is not None:
        output = imputed_series(data = new_df, metadata = meta)
    else: 
        output = None
    return output
    