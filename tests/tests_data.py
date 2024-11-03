import pytest
import pandas as pd
import json
import os


raw_json = open("./settings/settings.json")
meta_json = json.load(raw_json)
data_path = meta_json["data_path"]
df = pd.read_csv(data_path)
df["period"] = pd.to_datetime(df["period"])

def test_column_names():
    names = ["period", "subba", "impute", "y"]
    for i in names:
        assert i in df.columns

def test_column_attribute():
    assert df["period"].dtype == "<M8[ns]"
    assert df["subba"].dtype == "O"
    assert df["impute"].dtype == "float64"
    assert df["y"].dtype == "float64"


def test_column_missing_values():
    assert not df['period'].isnull().values.any()
    assert not df['subba'].isnull().values.any()
    assert not df['y'].isnull().values.any()

def test_num_rows():
    assert len(df) > 0

def test_duplicated():
    assert not df.duplicated().any()

