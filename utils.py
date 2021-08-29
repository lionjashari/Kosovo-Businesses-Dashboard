import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import geopandas as gpd
import pyproj
import datetime
from dateutil.relativedelta import relativedelta
from lifelines import KaplanMeierFitter


def choose_color(i):
    base_colors = [
        {"red": 57, "green": 106, "blue": 177},
        {"red": 218, "green": 124, "blue": 48},
        {"red": 62, "green": 150, "blue": 81},
        {"red": 204, "green": 37, "blue": 41},
        {"red": 83, "green": 81, "blue": 84},
        {"red": 107, "green": 76, "blue": 154},
        {"red": 146, "green": 36, "blue": 40},
        {"red": 148, "green": 139, "blue": 61}
    ]
    if i < len(base_colors):
        return f'rgb({base_colors[i]["red"]}, {base_colors[i]["green"]}, {base_colors[i]["blue"]})'
    base_color = i % len(base_colors)
    multiplier = int(i / len(base_colors))
    substract = multiplier * 5
    return f'rgb({base_colors[base_color]["red"] - substract}, {base_colors[base_color]["green"] - substract}, {base_colors[base_color]["blue"] - substract})'


def check_col_names(f):
    def w_function(*args, **kwargs):
        x_name = None if "x_name" not in kwargs or len(args) < 6 else kwargs["x_name"]
        y_names = None
        if "y_names" in kwargs:
            y_names = kwargs["y_names"]
        elif len(args) > 6:
            y_names = args[6]
        x_col = args[1] if "x_col" not in kwargs else kwargs["x_col"]
        y_cols = args[2] if "y_cols" not in kwargs is None else kwargs["y_cols"]

        x_name = x_col if x_name is None else x_name

        if y_names is None:
            return f(*args, **kwargs, x_name=x_name, y_names=y_cols)
        elif not isinstance(y_names, list):
            raise TypeError("y_names is not a list.")
        elif len(y_names) != len(y_cols):
            raise ValueError("the length of y_cols and y_names does not match")
        return f(*args, **kwargs)

    return w_function


@check_col_names
def plot_bars(
        graph_data,
        x_col,
        y_cols,
        title=None,
        y_names=None,
        orientation="v"):
    fig = go.Figure()
    for i, y_col in enumerate(y_cols):
        fig.add_trace(go.Bar(
            x=graph_data[x_col],
            y=graph_data[y_col],
            name=y_names[i],
            marker_color=choose_color(i),
            orientation=orientation
        ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    if title is not None:
        fig.update_layout(title={
            "text": title,
            "xanchor": "center",
            "yanchor": "top",
            "y": 0.9,
            "x": 0.5,
        })
    fig.update_xaxes(gridcolor="#d3d3d3")
    fig.update_yaxes(gridcolor="#d3d3d3")
    return fig


@check_col_names
def plot_lines(
        graph_data,
        x_col,
        y_cols,
        title=None,
        y_names=None,
        orientation="v"):
    fig = go.Figure()
    for i, y_col in enumerate(y_cols):
        fig.add_trace(go.Line(
            x=graph_data[x_col],
            y=graph_data[y_col],
            name=y_names[i],
            marker_color=choose_color(i),
            orientation=orientation
        ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    if title is not None:
        fig.update_layout(title={
            "text": title,
            "xanchor": "center",
            "yanchor": "top",
            "y": 0.9,
            "x": 0.5,
        })
    fig.update_xaxes(gridcolor="#d3d3d3")
    fig.update_yaxes(gridcolor="#d3d3d3")
    return fig


def plot_donut(labels, values):
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.45
    ))
    colors = [choose_color(i) for i in range(len(labels))]
    colors = [x for _, x in sorted(zip(values, colors), reverse=True)]
    fig.update_traces(marker=dict(colors=colors))
    return fig


def _read_kosovo_shapefile():
    shp_path = "shapes/kosovo_municipalities_1.shp"
    shp_file = gpd.read_file(shp_path, encoding='utf-8')
    shp_file.at[32, "JKOMUNA"] = "Prishtinë"
    shp_file.at[35, "JKOMUNA"] = "Kamenicë"
    corrected_names = {
        "Novoberdë": "Novobërdë",
        "Zubin potok": "Zubin Potok",
        "Shterpcë": "Shtërpcë",
        "Vushtri": "Vushtrri"
    }
    shp_file["JKOMUNA"] = shp_file["JKOMUNA"].apply(
        lambda x: corrected_names[x] if x in corrected_names else x
    )
    shp_file.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    return shp_file


def map_by_region(
        data,
        region_column,
        col_column,
        reverse=False,
        legend_title=None,
        show_percentage=True):
    shp_file = _read_kosovo_shapefile()
    shp_file = shp_file.merge(data,
                              how="outer",
                              left_on="JKOMUNA",
                              right_on=region_column)
    if show_percentage:
        tick_format = "%d %B (%a)<br>%Y"
        shp_file["_HoverData"] = round(shp_file["FailureRate"] * 100, 2)
    else:
        tick_format = ",d"
        shp_file["_HoverData"] = shp_file["FailureRate"]
    fig = px.choropleth(
        shp_file,
        geojson=shp_file.geometry,
        color=col_column,
        locations=shp_file.index,
        color_continuous_scale=px.colors.diverging.RdYlGn,
        hover_data=["Region", "_HoverData"],
        labels="Hello"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        coloraxis={
            "reversescale": reverse,
            "showscale": True
        },
        coloraxis_colorbar={
            'title': '% Businesses Failed',
            "x": 1,
            "yanchor": "middle",
            "xpad": 0,
            "ypad": 0,
            "tickformat": tick_format
        }
    )
    fig.update_traces(
        name="Region",
        hovertemplate="<br>".join([
            "<b>%{customdata[0]}</b>",
            f"{legend_title}: %{{customdata[1]}}%"
        ])
    )
    shp_file.drop("_HoverData", axis=1)
    return fig


def unix_time_millis(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds()


def get_marks_from_start_end(start, end):
    result = []
    current = start
    while current <= end:
        result.append(current)
        current += relativedelta(months=12)
    return {int(unix_time_millis(m)): {"label": str(m.year)} for m in result}


def plot_groups(groups):
    fig = make_subplots(rows=len(groups), cols=1)
    for group in groups:
        fig.add_trace(plot_bars(
            group,
            x_col="MonthEndDate",
            y_cols=["NumberClosed", "NumberNew"],
            title=None,
            y_names=["# Businesses closed", "# New businesses"]
        ))
    return fig


def plot_histogram(data, col, number_bins=30):
    return px.histogram(data, x=col, histnorm="probability density", nbins=number_bins)


def plotly_km(data):
    kmf = KaplanMeierFitter()
    tmp_data = data.data[["Failed", "MonthsFailure"]].dropna()
    kmf.fit(tmp_data["MonthsFailure"], event_observed=tmp_data["Failed"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=kmf.survival_function_.index, y=kmf.survival_function_['KM_estimate'],
        line=dict(shape='hv', width=3, color='rgb(31, 119, 180)'),
        showlegend=False
    ))
    # fig.add_trace(go.Scatter(
    #     x=kmf.confidence_interval_.index,
    #     y=kmf.confidence_interval_['KM_estimate_upper_0.95'],
    #     line=dict(shape='hv', width=0),
    #     showlegend=False,
    # ))
    #
    # fig.add_trace(go.Scatter(
    #     x=kmf.confidence_interval_.index,
    #     y=kmf.confidence_interval_['KM_estimate_lower_0.95'],
    #     line=dict(shape='hv', width=0),
    #     fill='tonexty',
    #     fillcolor='rgba(31, 119, 180, 0.4)',
    #     showlegend=False
    # ))

    fig.update_layout(
        xaxis_title="Duration",
        yaxis_title="Survival probability"
    )
    return fig
