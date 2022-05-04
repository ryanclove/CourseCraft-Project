import sqlalchemy.exc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from web.app.ccapp import app
from web.data.dbconnector import DBConnector
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import datetime
import navbar
from web.data.user import Major

CCDB = DBConnector()

layout = (
    html.Div(navbar.dean_navbar),
    html.Div(id="dean_layout"),
    html.Div(id="student-loader")
)


# Renders the dean homepage based on session data.
@app.callback(
    Output("dean_layout", "children"),
    Input("student-loader", "children"),
    Input("session-account", "data")
)
def dean_layout(loader, account):
    return dbc.Container(
        [
            html.H1(f"Welcome, {account['name']}", className="display-4 lead"),
            html.Hr(className="mt-2 mb-5"),
            html.Div(children=[
                html.Strong("Email:"),
                html.Span(f"{account['email']}", id="email", className="ms-3")
            ],
                className="mt-3"
            )
        ],
        className="container-fluid lg py-5",
    )


create_course_layout = (
    html.Div(navbar.dean_navbar),
    dbc.Container(children=[
        html.H1("Create Course", className="display-4 lead"),
        html.Hr(className="mt-2 mb-5"),
        dbc.Row([
            html.H4("Course Name"),
            dcc.Input(id="course-name"),

        ],
            className="mb-5"),
        html.H4("Major"),
        dbc.Row([
            dcc.Dropdown(
                id="course-major",
                options=[
                    u.name.capitalize() for u in Major
                ],
            ),
        ], className="mb-5"),

        html.H4("Weekly Meeting Days"),
        dbc.Row(
            dcc.Dropdown(
                id="meeting-days",
                options=[
                    'Select', 'Mon/Wed', 'Tue/Thu', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'
                ],
                value='Select'
            ),
            className="mb-5"),
        dbc.Row([
            html.H4("Pick Class Start Time"),
            html.Label('Pick Hour'),
            dcc.Dropdown(
                id="hour",
                options=[
                    hour for hour in range(7, 21)
                ]
            ),
            html.Label('Pick Minute'),
            dcc.Dropdown(
                id="minute",
                options=[
                    minute for minute in range(0, 60, 5)
                ]
            )], className="mb-5"),
        html.H4('Class Length'),
        dcc.RadioItems(
            id="class-length",
            options=[
                {'label': 'Single Period', 'value': 80},
                {'label': 'Double Period', 'value': 180},
                {'label': 'Recitation', 'value': 55}
            ],
            value="Single Period",
            className="mb-5"),
        dbc.Row([
            html.H4("Class Start and End Date"),
            dcc.DatePickerRange(id='date',
                                min_date_allowed=datetime.date(2020, 1, 1),
                                max_date_allowed=datetime.date(2030, 1, 1),
                                initial_visible_month=datetime.date(2022, 1, 1),
                                )
        ], className="mb-4"),
        dbc.Row([
            dbc.Button(
                "submit",
                id="submit-course"
            ),
        ],
            className="md mt-5"
        ),
        dbc.Row(
            id="course-update-status"
        ),
    ],
        className="lg mt-5"
    )
)


# allows a dean to create a new course in the database
@app.callback(
    Output("course-update-status", "children"),
    Input("submit-course", "n_clicks"),
    State("course-name", "value"),
    State("course-major", "value"),
    State("meeting-days", "value"),
    State("hour", "value"),
    State("minute", "value"),
    State("class-length", "value"),
    State("date", "start_date"),
    State("date", "end_date")
)
def submit_course(n_clicks, name, major, meeting_days, hour, minute, class_length, start_date, end_date):
    if not n_clicks:
        raise PreventUpdate()
    else:
        if not name and major == "Select":
            return dbc.Alert("Please enter the Course Name and Major")
        elif not name:
            return dbc.Alert("Please enter the Course Name")
        elif major == "Select":
            return dbc.Alert("Please select a major")
        elif meeting_days == "Select":
            return dbc.Alert("Please select Meeting Days")
        elif hour == "Select":
            return dbc.Alert("Please select Start Hour")
        elif minute == "Select":
            return dbc.Alert("Please select Start Minute")
        elif start_date is None:
            return dbc.Alert("Please select Start Date")
        elif end_date is None:
            return dbc.Alert("Please select End Date")
        else:
            try:
                start_time = datetime.time(hour, minute)
                hour = hour + (class_length // 60)
                minute = (minute + class_length) % 60
                end_time = datetime.time(hour, minute)
                result = CCDB.create_class(name, major, meeting_days, start_date, end_date, str(start_time),
                                           str(end_time))
                if result:
                    return dbc.Alert("Course Entered Successfully")
                else:
                    return dbc.Alert("Database Error")
            except sqlalchemy.exc.IntegrityError as e:
                return dbc.Alert(f"{name} already exists")
