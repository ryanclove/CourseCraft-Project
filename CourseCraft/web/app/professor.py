import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import State
from dash import Input, Output, dash_table, callback
from dash.exceptions import PreventUpdate

from web.data.dbconnector import DBConnector

from web.app import navbar
from web.app.ccapp import app

CCDB = DBConnector()

layout = [
    html.Div(id="professor-layout"),
    html.Div(id="professor-loader"),
]

register_layout = [
    html.Div(id='register_to_teach_layout'),
    html.Div(id="professor-loader"),
]


# Renders the professor homepage based on session data.
# "professor-loader" is a dummy input that ensures this callback is fired when the page loads.
@app.callback(
    Output("professor-layout", "children"),
    Input("professor-loader", "children"),
    State("session-account", "data")
)
def generate_layout(loader, account):
    return [
        html.Div(navbar.professor_navbar(account)),
        dbc.Container(
            [
                html.H1(f"Welcome, {account['name']}!", id="name_header", className="display-4 lead"),
                html.Hr(className="mt-2 mb-5"),
                html.Div(children=[
                    html.Strong("Email: ", className=""),
                    html.Span(account["email"], id="email", className="ms-3")
                ],
                    className="mt-3"
                )
            ],
            className="container-fluid lg py-5",
        ),
    ]


# returns a table with all classes that are available to register to teach
@app.callback(
    Output("register_to_teach_layout", "children"),
    Input("professor-loader", "children"),
    State("session-account", "data")
)
def register_to_teach(loader, account):
    df = CCDB.find_empty_classes()
    if not df.empty:
        df = df.rename(columns={"class_name": "id"})
        return [
            html.Div(navbar.professor_navbar(account)),
            dbc.Container(children=[
                dbc.Label('Click a cell in the table:'),
                dash_table.DataTable(df.to_dict('records'), id='tbl'),
                dbc.Alert(id='tbl_out'),
                dbc.Row([
                    dbc.Button(
                        "register",
                        id="register-course"
                    ),
                ]),
                dbc.Row(
                    id="register-update-status"
                ),
            ]
            ),
        ]
    else:
        return [
            html.Div(navbar.professor_navbar(account), className="mb-5"),
            dbc.Alert(children="No available courses at this time", className="text-center"),
        ]


# registers a professor to teach a class and stores it in the database
@callback(
    Output("register-update-status", "children"),
    Input("register-course", "n_clicks"),
    State('tbl', 'active_cell'),
    State("session-account", "data"),
)
def register_for_course_teaching(n_clicks, active_cell, account):
    if not n_clicks or not active_cell:
        raise PreventUpdate()
    else:
        active_row_id = active_cell['row_id']
        account_id = account['id']
        try:
            CCDB.teach_class(account_id, active_row_id)
        except ConnectionError:
            return dbc.Alert("Database Error")
        finally:
            return dbc.Alert("Registration Entered Successfully")
