import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from web.app import navbar
from web.app.ccapp import app
from web.data.dbconnector import DBConnector
from web.data.user import UserType

CCDB = DBConnector()

layout = html.Div(id="login-redirect-div",
                  children=[
                      navbar.login_navbar,
                      dbc.Container([
                          dbc.Row(
                              [
                                  html.H1("CourseCraft Login"),
                              ], className="mb-4"
                          ),

                          dbc.Row([
                              html.Label("Account Type:"),
                          ]),
                          dbc.Row([
                              dcc.Dropdown(
                                  id="login-user-types",
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
                                  id="login-email",
                                  autoFocus=True
                              )
                          ], className="mb-4"),

                          dbc.Row([
                              html.Label("Password")
                          ]),
                          dbc.Row([
                              dcc.Input(
                                  id="login-password",
                                  type="password"
                              )
                          ], className="mb-4"),

                          dbc.Row(
                              id="alert"
                          ),
                          dbc.Row([
                              dbc.Button(
                                  "Login",
                                  id="login-button",
                                  className="mb-2",
                              )
                          ]),
                          dbc.Row([
                              dbc.Button(
                                  "Create an Account",
                                  id="create-account-button",
                                  className="mb-2",
                                  href="/create_account"
                              )
                          ])
                      ], className="lg mt-5")

                  ]
                  )


# Verify the user's login credentials.
# If the credentials are valid, store them in session memory.
@app.callback(
    Output("session-account", "data"),
    Input("login-button", "n_clicks"),
    State("login-user-types", "value"),
    State("login-email", "value"),
    State("login-password", "value"),
)
def store_name(n_clicks, user_type, email, password):
    if not n_clicks or not email or not password:
        raise PreventUpdate()

    role = UserType[user_type.upper()]
    account = CCDB.find_user(email, password, role)
    if account:
        return account.__dict__
    raise PreventUpdate()


# After logging in, move to the user's homepage.
# This callback is executed only after session-account is updated after a valid login.
@app.callback(
    Output("alert", "children"),
    Input("login-button", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
)
def login(n_clicks, email, password):
    if not n_clicks:
        raise PreventUpdate()
    else:
        if not email and not password:
            return (
                dbc.Alert("Please enter email and password", className="alert-warning")
            )
        elif not email:
            return (
                dbc.Alert("Please enter email", className="alert-warning")
            )
        elif not password:
            return (
                dbc.Alert("Please enter password", className="alert-warning")
            )
        else:  # incorrect email/password
            return dbc.Alert("Invalid email, password, and/or role type", className="alert-warning")


# After logging in, move to the user's homepage.
# This callback is executed only after session-account is updated after a valid login.
@app.callback(
    Output("url", "pathname"),
    Input("session-account", "data"),
    State("login-user-types", "value"),
    State("login-email", "value"),
    State("login-password", "value"),
)
def login(account, user_type, email, password):
    if not email or not password:
        raise PreventUpdate()
    if user_type == "Student":
        return "/student"
    elif user_type == "Professor":
        return "/professor"
    elif user_type == "Dean":
        return "/dean"
