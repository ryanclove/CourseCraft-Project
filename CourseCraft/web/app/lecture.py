import base64
import os

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import sqlalchemy.exc
from dash import dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from web.app import navbar, login
from web.app.ccapp import app
from web.data.ccemail import send_submission
from web.data.dbconnector import DBConnector

layout = [
    html.Div(id="lecture-layout"),
    html.Div(id="student-loader"),
]

CCDB = DBConnector()


# returns the lecture layout based on the class name in the url path
@app.callback(
    Output("lecture-layout", "children"),
    Input('url', 'pathname'),
    State("session-account", "data")
)
def lecture_layout(url, account):
    if account is None:
        return login.layout
    lecture = url.strip("lecture/").replace("%20", " ")
    result = None
    try:
        result = CCDB.get_assignments(lecture)
    except sqlalchemy.exc.IntegrityError as e:
        pass
    return (
        navbar.student_navbar(account),
        dbc.Container(
            [
                html.H1(f"{lecture}", className="display-4 lead"),
                html.Hr(),
            ],
            className="mt-5 mb-5"
        ),
        html.Div([
            dcc.Tabs(
                id="student_tabs",
                value="submit_assignments",
                children=[
                    dcc.Tab(label="View/Submit Assignments", value="submit_assignments"),
                    dcc.Tab(label="Grades", value="graded_assignments"),
                ]),
            html.Div(
                id="students_tabs_content"
            ),
        ],
        ),
    )


# Generates the two tab layout containing the assignment lis tab and graded assignments tab
@app.callback(
    Output("students_tabs_content", "children"),
    Input("student_tabs", "value"),
    Input('url', 'pathname'),
    State("session-account", "data"))
def generate_students_tabs(tab, url, account):
    lecture = url.strip("lecture/").replace("%20", " ")
    student_id = account['id']
    result = None
    try:
        result = CCDB.get_assignments(lecture)
        graded = CCDB.get_my_grades(student_id, lecture)
    except sqlalchemy.exc.IntegrityError as e:
        pass
    if tab == "submit_assignments":
        return dbc.Container([
            html.Br(),
            html.H4("Assignment List"),
            dash_table.DataTable(id="table",
                                 columns=[
                                     {'name': "Assignment", 'id': 'assignment_name', 'type': 'text', 'editable': False},
                                     {'name': "File", 'id': 'file_name', 'type': 'text', 'editable': False},
                                     {'name': 'Due Date', 'id': 'due_date', 'type': 'datetime', 'editable': False},
                                 ],
                                 data=result.to_dict('records')
                                 ),
            html.Br(),
            dbc.Button(id="btndownload", children="Download Project Instructions File"),
            dcc.Download(id="download-project"),
            html.Br(),
            html.Div(children=[
                html.Hr(),
                html.H4("Select an assignment to submit"),
                dbc.Alert(id="assignment-name", className="dark", children="None Selected"),
                html.Div(id="assignment-id", style={'display': 'none'}),
                html.Div(id="upload-status"),
                html.A(id="link"),
                dcc.Upload(id="upload", children=[
                    dbc.Button(id="submit", children="Submit")
                ])
            ], className="mt-5")

        ], className="md"
        )

    if tab == "graded_assignments":
        return dbc.Container(
            children=[
                html.Br(),
                html.H4("Graded Assignments"),
                dash_table.DataTable(id="my_submissions_table",
                                     data=graded.to_dict('records'),
                                     editable=False,
                                     columns=[
                                         {'name': "Assignment", 'id': 'assignment_name', 'type': 'text',
                                          'editable': False},
                                         {'name': "File Submitted", 'id': 'submitted_file', 'type': 'text',
                                          'editable': False},
                                         {'name': 'Grade', 'id': 'grade', 'type': 'text', 'editable': False},
                                     ],
                                     ),
                html.Br(),
            ],
        )


# allows you to download posted assignments by selecting the row of the assignment you want to download
@app.callback(
    Output("download-project", "data"),
    Input("table", "active_cell"),
    Input("table", "data"),
    State('url', 'pathname'),
    Input("btndownload", "n_clicks")
)
def view_project_file(active_cell, data, url, n_clicks):
    if not n_clicks:
        raise PreventUpdate()
    else:
        lecture = url.strip("lecture/").replace("%20", " ")
        if active_cell:
            row = active_cell['row']
            project_file = data[row]['file_name']
            assignment_name = data[row]['assignment_name']
            directory = f"assignments/{lecture}/{assignment_name}/{project_file}"
            if os.path.exists(directory):
                return dcc.send_file(directory)
            else:
                try:
                    with open(f"assignments/{lecture}/{assignment_name}/{assignment_name} Instructions.txt", 'w') as f:
                        f.write(project_file)
                except FileNotFoundError:
                    pass
            directory = f"assignments/{lecture}/{assignment_name}/{assignment_name} Instructions.txt"
            return dcc.send_file(directory)
        else:
            return


# stores the chosen assignment from the table in session memory
@app.callback(
    Output("assignment-name", "children"),
    Output("assignment-name", "className"),
    Output("assignment-id", "children"),
    Input("table", "active_cell"),
    Input("table", "data")
)
def pick_assignment(active_cell, data):
    if active_cell:
        row = active_cell['row']
        assignment = data[row]['assignment_name']
        id = data[row]['assignment_id']
        return f"{assignment} selected", "alert-success", id
    else:
        return "None Selected", "alert-info", ""


# allows a student to upload an assignment into the coursecraft local directory
@app.callback(
    Output("upload-status", "children"),
    Input("assignment-name", "children"),
    Input("assignment-id", "children"),
    Input("upload", "contents"),
    State("upload", "filename"),
    State('url', 'pathname'),
    State("session-account", "data"),
    Input("submit", "n_clicks")
)
def submit_assignment(assignment, assignment_id, content, filename, url, user, n_click):
    if not n_click:
        raise PreventUpdate()
    if assignment == "None Selected":
        return dbc.Alert(f"No assignment selected ", className="alert-warning")
    elif assignment_id == -1:
        return dbc.Alert(f"Assignment overdue ", className="alert-warning")
    elif not content:
        return dbc.Alert(f"No file selected ", className="alert-warning")
    else:
        # create new directory if needed
        lecture = url.strip("lecture/").replace("%20", " ")
        assignment = assignment.replace(" selected", "")
        student_id = user['id']
        directory = f"submitted/{lecture}/{assignment}/{student_id}"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # make entry into grade table
        CCDB.submit_assignments(assignment_id, student_id, filename)

        # Write to file
        data = content.encode("utf8").split(b";base64,")[1]

        with open(f"{directory}/{filename}", 'wb') as f:
            f.write(base64.decodebytes(data))

        # Notify the student that their assignment was submitted successfully
        send_submission(assignment_id, student_id)
        return 0, dbc.Alert("Successfully Uploaded")
