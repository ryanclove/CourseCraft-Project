import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from web.app import navbar
from web.app.ccapp import app
from web.data.dbconnector import DBConnector
from web.data.user import UserType, Major

CCDB = DBConnector()

layout = html.Div(
    [
        navbar.login_navbar,
        dbc.Container([

            dbc.Row(
                [
                    html.H1("Create Your Account"),
                ], className="mb-4"
            ),

            dbc.Row([
                html.Label("Account Type:"),
            ]),
            dbc.Row([
                dcc.Dropdown(
                    id="create-account-types",
                    options=[
                        u.name.capitalize() for u in UserType
                    ],
                    value=UserType.STUDENT.name.capitalize(),
                ),
            ], className="mb-4"),

            dbc.Row([
                html.Label("Email:")
            ]),
            dbc.Row([
                dcc.Input(
                    id="create-account-email",
                    autoFocus=True
                )
            ], className="mb-4"),

            dbc.Row([
                html.Label("Password:")
            ]),
            dbc.Row([
                dcc.Input(
                    id="create-account-password",
                    type="password"
                )
            ], className="mb-4"),

            dbc.Row([
                html.Label("Confirm Password:")
            ]),
            dbc.Row([
                dcc.Input(
                    id="create-account-confirm-password",
                    type="password"
                )
            ], className="mb-4"),

            dbc.Row([
                html.Label("Full Name:")
            ]),
            dbc.Row([
                dcc.Input(
                    id="create-account-full-name",
                )
            ], className="mb-4"),

            dbc.Container([
                dbc.Row([
                    html.Label("Major:")
                ]),
                dbc.Row([
                    dcc.Dropdown(
                        id="create-account-majors",
                        options=[
                            m.name.capitalize() for m in Major
                        ],
                        value=Major.CS.name.capitalize(),
                    )
                ], className="mb-4"),
            ], id="create-account-major-container"),

            dbc.Row(
                id="create-account-alert"
            ),
            dbc.Row([
                dbc.Button(
                    "Create Account",
                    id="create-account-button",
                    className="mb-2"
                )
            ]),
            dbc.Row([
                dbc.Button(
                    "Return to Login Screen",
                    id="return-to-login-button",
                    className="mb-2",
                    href="/login"
                )
            ])

        ], className="lg mt-5")
    ]
)


# Create a user account if the chosen email isn't already taken
@app.callback(
    Output("create-account-alert", "children"),
    Input("create-account-button", "n_clicks"),
    State("create-account-types", "value"),
    State("create-account-email", "value"),
    State("create-account-password", "value"),
    State("create-account-confirm-password", "value"),
    State("create-account-full-name", "value"),
    State("create-account-majors", "value")
)
def create_account(n_clicks, user_type, email, password, confirm_password, name, major):
    # Validate input
    if not n_clicks:
        raise PreventUpdate()
    if not (email and password and confirm_password and name):
        return dbc.Alert("Your account information is incomplete.", className="alert-warning")
    if password != confirm_password:
        return dbc.Alert("Your password strings do not match.", className="alert-warning")
    # Create the account
    if user_type == UserType.STUDENT.name.capitalize():
        result = CCDB.create_user(email, password, user_type, name, major)
    else:
        result = CCDB.create_user(email, password, user_type, name)
    if result:
        return dbc.Alert(f"Account successfully created for {name}!")
    else:
        return dbc.Alert("A user with that email already exists.", className="alert-warning")


# Show the major selector for a student account
@app.callback(
    Output("create-account-major-container", "hidden"),
    Input("create-account-types", "value")
)
def show_majors(user_type):
    if user_type == UserType.STUDENT.name.capitalize():
        return False
    else:
        return True
