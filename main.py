import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import styles
from utils import plot_bars, plot_lines, map_by_region, plot_groups, plot_histogram, plotly_km
from data import Dataset
from dash.dependencies import Input, Output

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dataset = Dataset()

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Analysis", href="")),
        dbc.NavItem(dbc.NavLink("Dataset", href="#"))
    ],
    brand="Why do businesses fail?",
    brand_href="",
    color="darkgrey",
    dark=True,
)

sidebar = html.Div([
    html.H3("Graph type"),
    dcc.RadioItems(
        id="graph-type",
        options=[
            {"label": "Barchart", "value": "bar"},
            {"label": "Map", "value": "map"},
            {"label": "Linechart", "value": "line"},
            #{"label": "Histogram", "value": "hist"},
            {"label": "Kaplan-Meier", "value": "kaplan-meier"}
        ],
        value="bar",
        labelStyle={"display": "block"}
    ),
    html.Div(id="sidebar-utilities")
], style=styles.sidebar)

bar_line_utilities = html.Div(children=[
    html.H3("Indicator"),
    dcc.Dropdown(
        id="graph-indicator-dd",
        options=[
            {"label": "# Registered and Failed", "value": "reg_fail"},
            {"label": "# Registered", "value": "reg"},
            {"label": "# Failed", "value": "fail"},
            {"label": "Failure rate", "value": "rate"}
        ],
        value="reg_fail",
        style=styles.dropdown
    ),
    html.Br(),
    # html.H3("Group by"),
    # dcc.Dropdown(
    #     id="group-bar-by",
    #     options=[{"label": x, "value": x} for x in dataset.data.columns],
    #     style=styles.dropdown
    # )
])

histogram_utilities = html.Div(children=[
    html.H3("Variable:"),
    dcc.Dropdown(
        id="group-bar-by",
        options=[{"label": x, "value": x} for x in dataset.data.columns],
        style=styles.dropdown
    ),
    html.Br(),
    html.H3("Number of Bins"),
    dcc.Slider(
        id="number-bins",
        min=1,
        max=100,
        step=1,
        value=30
    ),
    html.H3(id="number-bins-label")
])

app.layout = html.Div(
    style=styles.main_page,
    children=[
        html.Div(children=[navbar]),
        html.Div(children=[
            sidebar,
            html.Div([dcc.Graph(id="main-graph")], style=styles.main_content_graph)
        ], style=styles.main_content)
    ]
)


@app.callback(
    Output("sidebar-utilities", "children"),
    Input("graph-type", "value")
)
def add_utilities(graph_type):
    if graph_type in ["bar", "line", "kaplan-meier"]:
        return bar_line_utilities
    elif graph_type == "hist":
        return histogram_utilities


# @app.callback(
#     Output("number-bins-label", "children"),
#     Output("main-graph", "figure"),
#     [
#         Input("number-bins", "value"),
#         Input("group-bar-by", "value")
#     ]
# )
# def update_number_bins(no_bins, group_by):
#     return no_bins, plot_histogram(dataset.data, col=group_by)


@app.callback(
    Output("main-graph", "figure"),
    [
        Input("graph-indicator-dd", "value"),
        Input("graph-type", "value")
    ]
)
def return_graph(indicator, graph_type):
    if graph_type in ["bar", "line"]:
        if indicator == "reg_fail":
            data, y_cols = dataset.number_registered_closed(), ["NumberClosed", "NumberNew"]
            title = "# Registered and closed businesses"
            y_names = ["# Businesses closed", "# New businesses"]
        elif indicator == "fail":
            data, y_cols = dataset.number_closed_per_period(), ["NumberClosed"]
            title = "# Closed businesses"
            y_names = ["# Businesses closed"]
        elif indicator == "reg":
            data, y_cols = dataset.number_new_per_period(), ["NumberNew"]
            title = "# Registered businesses"
            y_names = ["# New businesses"]
        else:
            return ValueError("Only 'reg_fail', 'reg' and 'fail' allowed.")

        plot_func = plot_bars if graph_type == "bar" else plot_lines
        fig = plot_func(
            graph_data=data, y_cols=y_cols, x_col="MonthEndDate", y_names=y_names, title=title
        )
        return fig

    if graph_type == "map":
        fig = map_by_region(
            dataset.failure_rate_by_region("2000-01-01", "2021-12-31"),
            region_column="Region",
            col_column="FailureRate",
            legend_title="% Businesses Failed",
            reverse=True
        )
        return fig
    # if graph_type == "hist":
    #     return plot_histogram(dataset.data, col=group_by)
    if graph_type == "kaplan-meier":
        return plotly_km(dataset)


if __name__ == '__main__':
    app.run_server(debug=True)
