import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.exceptions import PreventUpdate
import dash
from dash import dcc, dash_table
from dash.dependencies import Input, Output, State
from web.app import navbar, login
from web.app.ccapp import app
from web.data.dbconnector import DBConnector

CCDB = DBConnector()

layout = [
    html.Div(id="student-layout"),
    html.Div(id="student-loader"),
]


# Renders the student homepage based on session data.
# "student-loader" is a dummy input that ensures this callback is fired when the page loads.
@app.callback(
    Output("student-layout", "children"),
    Input("student-loader", "children"),
    State("session-account", "data")
)
def generate_layout(loader, account):
    if account is None:
        return login.layout
    return [
        html.Div(navbar.student_navbar(account)),
        dbc.Container(
            [
                html.H1(f"Welcome, {account['name']}!", id="name_header", className="display-4 lead"),
                html.Hr(className="mt-2 mb-5"),
                html.Div(children=[
                    html.Strong("Email: ", className=""),
                    html.Span(account["email"], id="email", className="ms-3")
                ],
                    className="mt-3"
                ),
                html.Div(children=[
                    html.Strong("Current GPA: ", className=""),
                    html.Span(account["gpa"], id="gpa", className="ms-3")
                ],
                    className="mt-3"
                )
            ],
            className="container-fluid lg py-5",
        ),
    ]


registration_layout = [
    html.Div(id="register_for_classes_layout"),
    html.Div(id="student-loader")
]


# Renders the course registration page based on the current student account data
@app.callback(
    Output("register_for_classes_layout", "children"),
    Input("student-loader", "children"),
    State("session-account", "data")
)
def generate_registration_layout(loader, account):
    available_courses = CCDB.get_available_classes(account['id'])

    if available_courses is not None:
        available_courses = rename_columns(available_courses)

        return [
            html.Div(navbar.student_navbar(account)),
            dbc.Container(children=[
                html.H1(f"Course Registration", className="display-4 lead"),
                html.Hr(className="mt-2 mb-5"),

                dbc.Row([
                    html.H2("Available Courses"),
                ]),

                dbc.Container([
                    dbc.Label("Select the courses you would like to register for:"),

                    html.Div([

                        dash_table.DataTable(
                            id='datatable-row-ids',
                            data=available_courses.to_dict('records'),
                            columns=[{"name": i, "id": i} for i in available_courses.columns],
                            style_cell={'textAlign': 'left'},
                            sort_mode='multi',
                            row_selectable='multi',
                            selected_rows=[],
                            page_action='native',
                            page_current=0,
                            page_size=10,
                        ),
                    ]),

                    dbc.Row(
                        id="registration-status"
                    ),

                    dbc.Row([
                        dbc.Button(
                            "Register",
                            id="register-button"
                        ),
                    ],
                        className="md mt-5"
                    ),

                ],
                    className="container-fluid lg py-5",
                )
            ]),
        ]
    else:
        return [
            html.Div(navbar.student_navbar(account)),
            dbc.Container(children=[
                html.H1(f"Course Registration", className="display-4 lead"),
                html.Hr(className="mt-2 mb-5"),

                dbc.Row([
                    html.H2("No courses available at this time"),
                ]),
            ])
        ]


# Handles course registration based on input from the dash table
@app.callback(
    Output("registration-status", "children"),
    Input("student-loader", "children"),
    Input("register-button", "n_clicks"),
    Input('datatable-row-ids', 'selected_rows'),
    State("session-account", "data")

)
def register(loader, n_clicks, selected_rows, account):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    available_classes = CCDB.get_available_classes(account['id'])
    selected = []

    if 'register-button' in changed_id:

        for row in selected_rows:
            selected.append(available_classes.iloc[row]['class_name'])

            if not selected:
                return dbc.Alert("Please select a course.", color="danger")
            else:

                try:
                    CCDB.course_registration(selected, account['id'])
                except ConnectionError:
                    return dbc.Alert("Database Error", color="danger")
                finally:
                    return dbc.Alert("Registration successful.", )


view_schedule_layout = [
    html.Div(id="schedule-layout"),
    html.Div(id="student-loader")
]


# Renders the students schedule page based on the students account data
@app.callback(
    Output("schedule-layout", "children"),
    Input("student-loader", "children"),
    State("session-account", "data")
)
def generate_schedule_layout(loader, account):
    df = CCDB.get_course_schedule(account['id'])
    df = rename_columns(df)

    return [

        html.Div(navbar.student_navbar(account)),
        dbc.Container(children=[
            html.H1(f"View Schedule", className="display-4 lead"),
            html.Hr(className="mt-2 mb-5"),

            html.H2("Daily View", style={"textAlign": "left"}),

            html.Div([

                dcc.Tabs(
                    id="daily_view_tabs",
                    value="monday_tab",
                    children=[
                        dcc.Tab(label="Monday", value="monday_tab"),
                        dcc.Tab(label="Tuesday", value="tuesday_tab"),
                        dcc.Tab(label="Wednesday", value="wednesday_tab"),
                        dcc.Tab(label="Thursday", value="thursday_tab"),
                        dcc.Tab(label="Friday", value="friday_tab"),
                    ]),
                html.Div(
                    id="tabs_content"
                ),

                html.Br()
            ]),
        ]),

        dbc.Container([
            html.Br(),
            html.Br(),

            html.H2("Weekly View", style={"textAlign": "left"}),

            html.Div([

                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={'textAlign': 'left'},
                ),
            ]),
            html.Br(),
        ])
    ]


# Rename columns helper function
def rename_columns(df):
    df = df.rename(columns={
        "class_name": "COURSE NAME",
        "major": "MAJOR",
        "classTime_days_of_week": "CLASS MEETING DAYS",
        "classTime_start_date": "START DATE",
        "classTime_end_date": "END DATE",
        "classTime_start_time": "CLASS START TIME",
        "classTime_end_time": "CLASS END TIME"})
    return df


# Renders the daily view schedule tabs based on student enrollment
@app.callback(
    Output("tabs_content", "children"),
    Input("daily_view_tabs", "value"),
    State("session-account", "data"))
def generate_daily_view_tabs(tab, account):
    if tab == "monday_tab":
        df = CCDB.get_daily_schedule(account['id'], "Monday")
        df = df.append(CCDB.get_two_day_schedule(account['id'], "Mon/Wed"))
        df = rename_columns(df)

        return html.Div([
            html.Br(),

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'})
        ])

    if tab == "tuesday_tab":
        df = CCDB.get_daily_schedule(account['id'], "Tuesday")
        df = df.append(CCDB.get_two_day_schedule(account['id'], "Tue/Thu"))
        df = rename_columns(df)

        return html.Div([
            html.Br(),

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'})
        ])

    if tab == "wednesday_tab":
        df = CCDB.get_daily_schedule(account['id'], "Wednesday")
        df = df.append(CCDB.get_two_day_schedule(account['id'], "Mon/Wed"))

        df = rename_columns(df)

        return html.Div([
            html.Br(),

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'})
        ])

    if tab == "thursday_tab":
        df = CCDB.get_daily_schedule(account['id'], "Thursday")
        df = df.append(CCDB.get_two_day_schedule(account['id'], "Tue/Thu"))
        df = rename_columns(df)

        return html.Div([
            html.Br(),

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'})
        ])

    if tab == "friday_tab":
        df = CCDB.get_daily_schedule(account['id'], "Friday")
        df = rename_columns(df)

        return html.Div([
            html.Br(),

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'})
        ])


calculate_future_gpa_layout = [
    html.Div(id="future-gpa-layout"),
    html.Div(id="student-loader")
]


# View for future gpa calculator
@app.callback(
    Output("future-gpa-layout", "children"),
    Input("student-loader", "children"),
    State("session-account", "data")
)
def generate_future_gpa(loader, account):
    return [

        html.Div(navbar.student_navbar(account)),
        dbc.Container(children=[
            html.H1(f"Calculate Future GPA", className="display-4 lead"),
            html.Hr(className="mt-2 mb-5"),
            dbc.Container([
                dbc.Row([
                    html.Label("How many credits?")
                ]),
                dbc.Row([
                    dcc.Input(
                        id="credits_wanted",
                        autoFocus=True
                    )
                ]),
                dbc.Row([
                    html.Label("What GPA would you like to achieve with that amount of credits?")
                ]),
                dbc.Row([
                    dcc.Input(
                        id="desired_gpa",
                        autoFocus=True
                    )
                ], className="mb-4"),
                dbc.Row(
                    id="alert_gpa"
                ),
                dbc.Row([
                    dbc.Button(
                        "Calculate",
                        id="calculate-button",
                        className="mb-2",
                    )
                ]),
            ], className="lg mt-5")

        ]
        )
    ]


# The actual method that calculates a future GPA.
def calculate_future_gpa_method(currentGpa, currCredit, credits_wanted, desired_gpa):
    currGpaCredits = currentGpa * currCredit
    return ((float(desired_gpa) * (currCredit + float(credits_wanted))) - currGpaCredits) / float(
        credits_wanted)


# The view/callback that accepts the inputs for future gpa.
@app.callback(
    Output("alert_gpa", "children"),
    Input("calculate-button", "n_clicks"),
    State("credits_wanted", "value"),
    State("desired_gpa", "value"),
    State("session-account", "data")
)
def calculate_future_gpa(n_clicks, credits_wanted, desired_gpa, account):
    if not n_clicks:
        raise PreventUpdate()
    else:
        if not credits_wanted and not desired_gpa:
            return (
                dbc.Alert("Please enter credits and desired gpa", className="alert-warning")
            )
        elif not credits_wanted:
            return (
                dbc.Alert("Please enter credits", className="alert-warning")
            )
        elif not desired_gpa:
            return (
                dbc.Alert("Please enter desired_gpa", className="alert-warning")
            )
        else:
            averageGpaNeeded = calculate_future_gpa_method(account["gpa"], account["credits_earned"], credits_wanted,
                                                           desired_gpa)
            if averageGpaNeeded > 4 or averageGpaNeeded < 0:
                return (
                    dbc.Alert("not possible with that amount of credits", className="alert-warning")
                )
            else:
                return (
                    dbc.Alert("{:.2f}".format(averageGpaNeeded), className="alert-warning")
                )


calculate_semester_gpa_layout = [
    html.Div(id="semester-gpa-layout"),
    html.Div(id="student-loader")
]


# Semester GPA calculator view page
@app.callback(
    Output("semester-gpa-layout", "children"),
    Input("student-loader", "children"),
    State("session-account", "data")
)
def generate_semester_gpa(loader, account):
    df = CCDB.get_enrolled_course(account['id'])
    df['course_credits'] = None
    df['likely_grade'] = None
    if not df.empty:
        return [
            html.Div(navbar.student_navbar(account)),
            dbc.Container(children=[
                html.H1(f"Calculate GPA After Current Semester", className="display-4 lead"),
                html.Hr(className="mt-2 mb-5"),
                dbc.Container([
                    dbc.Label('Write your credit amount per class and your likely grade then press calculate.'),
                    dash_table.DataTable(
                        data=df.to_dict('records'),
                        editable=True,
                        columns=[{"name": i, "id": i} for i in df.columns],
                        id='tbl'),
                    dbc.Alert(id='tbl_out'),
                    dbc.Row(
                        id="alert_semester_gpa"
                    ),
                    dbc.Row([
                        dbc.Button(
                            "Calculate",
                            id="calculate-button-semester",
                            className="mb-2",
                        )
                    ]),
                ], className="lg mt-5")
            ])
        ]
    else:
        return [
            html.Div(navbar.student_navbar(account), className="mb-5"),
            dbc.Alert(children="No available courses at this time", className="text-center"),
        ]


# The actual method that does the calculations for semester GPA
def calculate_semester_gpa_method(grades, currentGpa, currCredit):
    semesterGpaCreds = sum(pd.to_numeric(grades.likely_grade) * pd.to_numeric(grades.course_credits))
    currGpaCredits = currentGpa * currCredit
    currCredit += (pd.to_numeric(grades['course_credits'])).sum()
    currGpaCredits = currGpaCredits + semesterGpaCreds

    return currGpaCredits / currCredit


# The view that accepts input for semester GPA
@app.callback(
    Output("alert_semester_gpa", "children"),
    Input("calculate-button-semester", "n_clicks"),
    State("tbl", "data"),
    State("tbl", "columns"),
    State("session-account", "data")
)
def calculate_semester_gpa(n_clicks, data, columns, account):
    valid_grade = ['0', '.5', '1', '1.5', '2', '2.5', '3', '3.5', '4']
    if not n_clicks:
        raise PreventUpdate()
    else:
        df = pd.DataFrame(data)
        if df['likely_grade'].isnull().values.any() or df['course_credits'].isnull().values.any():
            return (
                dbc.Alert("one of your grades or credits is null", className="alert-warning")
            )
        elif not df['likely_grade'].str.isnumeric().values.any() or not df[
            'course_credits'].str.isnumeric().values.any():
            return (
                dbc.Alert("one of your grades or credit is not numeric", className="alert-warning")
            )
        elif not df['likely_grade'].isin(valid_grade).all():
            return (
                dbc.Alert("Only 0 -> 4 are valid entries in .5 intervals", className="alert-warning")
            )
        else:
            df = pd.DataFrame(data)
            semesterGpa = calculate_semester_gpa_method(df, account['gpa'], account["credits_earned"])
            return (
                dbc.Alert("{:.2f}".format(semesterGpa), className="alert-warning")
            )
