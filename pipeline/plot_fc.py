import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import datetime
import great_tables as gt



def plot_forecast(days = 3, settings_path = "../settings/settings.json"):
    raw_json = open(settings_path)

    meta_json = json.load(raw_json)
    meta_path = meta_json["meta_path"]
    data_path = meta_json["data_path"]
    forecast_path = meta_json["forecast_path"]
    forecast_log_path = meta_json["forecast_log_path"]

    data = pd.read_csv(data_path)
    data["period"] = pd.to_datetime(data["period"])

    fc = pd.read_csv(forecast_path)
    fc["ds"] = pd.to_datetime(fc["ds"])

    fc_log = pd.read_csv(forecast_log_path)

    for i in ["refresh_time", "start", "end"]:
        fc_log[i] = pd.to_datetime(fc_log[i])


    end_date = data["period"].max()
    start_date = end_date -  datetime.timedelta(days = days)
    meta = pd.read_csv(meta_path)
    
    fc_map = pd.DataFrame(fc_log.groupby(["unique_id"])["start"].max())
    fc_map["unique_id"] = fc_map.index
    fc_map.reset_index(inplace = True, drop = True)
    
    fc_map["color"] = px.colors.qualitative.Light24[0:len(fc_map)]

    p = go.Figure()


    for index, row in fc_map.iterrows():
        subba = row["unique_id"]
        c = row["color"]
        start_act = row["start"]
        label = fc_log[(fc_log["start"] == start_act) & (fc_log["unique_id"] == subba)]["label"].iloc[0]

        f = fc[(fc["unique_id"] == subba) & (fc["label"] == label)]
        end_date = max(end_date, f["ds"].max())
        d = data[data["subba"] == subba]

        p = p.add_scatter(name = "Actual",
                          legendgroup= subba+ "_actual",
                          legendgrouptitle_text=subba + " Forecast",
                          x = d["period"],
                          y = d["value"],
                          mode = "lines",
                          line= dict(color= c))
        p = p.add_scatter(name= "Forecast",
                          legendgroup= subba+ "_forecast",
                          x = f["ds"],
                          y = f["forecast"],
                          mode = "lines",
                          line= dict(color= c, dash = "dash"),
                          showlegend= True)
        p = p.add_scatter(name= subba + " PI",
                          legendgroup= subba+ "_forecast",
                          x= f["ds"], 
                          y= f["upper"],
                          mode='lines',
                          marker=dict(color="#444"),
                          line=dict(width=0),
                          showlegend=False)
        p = p.add_scatter(name= subba + " PI",
                          legendgroup= subba+ "_forecast",
                          x= f["ds"], 
                          y= f["lower"],
                          mode='lines',
                          marker=dict(color="#444"),
                          line=dict(width=0),
                          fillcolor='rgba(68, 68, 68, 0.3)',
                          fill='tonexty',
                          showlegend=False)




    p = p.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7,
                         label="7d",
                         step="day",
                         stepmode="backward"),
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            ),

            type="date",
            range=[start_date,end_date]
        )
    )

    return p