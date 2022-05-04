import base64
import os
from datetime import datetime

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import sqlalchemy.exc
from dash import dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from web.app import navbar, login
from web.app.ccapp import app
from web.data.ccemail import send_assignment, send_grades, send_announcement
from web.data.dbconnector import DBConnector

layout = [
    html.Div(id="prof-lecture-layout"),
    html.Div(id="professor-loader"),
]

CCDB = DBConnector()


# returns the lecture layout based on the class name in the url path
@app.callback(
    Output("prof-lecture-layout", "children"),
    Input('url', 'pathname'),
    State("session-account", "data")
)
def prof_lecture_layout(url, account):
    if account is None:
        return login.layout
    lecture = url.strip("prof-lecture/").replace("%20", " ")
    result = None
    try:
        result = CCDB.get_assignments(lecture)
    except sqlalchemy.exc.IntegrityError as e:
        pass
    return (
        navbar.professor_navbar(account),
        dbc.Container(
            [
                html.H1(f"{lecture}", className="display-4 lead"),
                html.Hr(),
            ],
            className="mt-5 mb-5"
        ),
        html.Div([

            dcc.Tabs(
                id="professor_tabs",
                value="create_announcement",
                children=[
                    dcc.Tab(label="Create Announcement", value="create_announcement"),
                    dcc.Tab(label="Create Assignments", value="create_assignments_tab"),
                    dcc.Tab(label="View/Grade Assignments", value="grade_assignments_tab"),
                ]),
            html.Div(
                id="profs_tabs_content"
            ),

            html.Br()
        ]),
    )


# returns the three tab layout containing the create announcement tab, create assignment tab, and grade assignment tab
@app.callback(
    Output("profs_tabs_content", "children"),
    Input("professor_tabs", "value"),
    Input('url', 'pathname'),
    State("session-account", "data"))
def generate_professors_tabs(tab, url, account):
    lecture = url.strip("prof-lecture/").replace("%20", " ")
    result = None
    try:
        result = CCDB.get_assignments(lecture)
    except sqlalchemy.exc.IntegrityError as e:
        pass
    if tab == "create_announcement":
        return dbc.Container(children=[
            html.Br(),
            html.H1("Create Announcement", className="h4"),
            html.Hr(className="mt-2 mb-5"),
            dbc.Row([
                html.Label("Announcement Subject:"),
                dcc.Input(id="prof-announcement-subject")
            ]
            ),
            dbc.Row([
                html.Label("Announcement Details: "),
                dcc.Input(id="prof-announcement-text")
            ]
            ),
            dbc.Row([
                dbc.Button(
                    "Create Announcement",
                    id="create-announcement"
                ),
            ],
                className="md mt-5"
            ),
            dbc.Row(
                id="announcement-update-status"
            ),
        ]
        )

    if tab == "create_assignments_tab":
        return dbc.Container(children=[
            html.H1("Create Assignment", className="h4"),
            html.Hr(className="mt-2 mb-5"),
            dbc.Row([
                html.Label("Assignment Name"),
                dcc.Input(id="prof-assignment-name")
            ]
            ),
            html.Label("Assignment Instructions"),
            dbc.Row([
                dcc.Input(id="prof-assignment-instructions"),
            ]),
            html.Div([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=False
                ),
                html.Div(id='uploaded-instructions'),
                html.Div(id='output-image-upload'),
            ]),

            html.Div([
                html.Label("Due Date"),
                dbc.Row([
                    dcc.DatePickerSingle(
                        date=datetime.now(),
                        display_format='M-D-Y',
                        id='date'
                    )
                ]),
            ]),
            dbc.Row([
                dbc.Button(
                    "Create Assignment",
                    id="create-assignment"
                ),
            ],
                className="md mt-5"
            ),
            dbc.Row(
                id="assignment-update-status"
            ),
        ],
            className="lg mt-5"
        )

    if tab == "grade_assignments_tab":
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
            html.Div(children=[
                html.Hr(),
                html.H4("Select an assignment to view submissions"),
                dbc.Alert(id="assignment_name", className="dark", children="None Selected"),
                html.Div(id="assignment_id", style={'display': 'none'}),
                html.Div(id="upload-status"),
                html.A(id="link"),
            ], className="mt-5"),
            dbc.Row([
                dbc.Button(
                    "View Submissions",
                    id="view-submissions"
                ),
                dbc.Row(
                    id="view-submissions-update-status"
                ),
            ],
            ),
            html.Div(id='submissions_table'),
            html.Div(id='grade-entered'),
            html.Div(id='grade-assignment'),
            dbc.Row(
                id="assignment-graded-status"
            ),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br()
        ])


# stores the chosen assignment in session memory
@app.callback(
    Output("assignment_name", "children"),
    Output("assignment_name", "className"),
    Output("assignment_id", "children"),
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


# stores the chosen submission in session memory
@app.callback(
    Output("submission_name", "children"),
    Output("submission_name", "className"),
    Output("submission_id", "children"),
    Input("submissions_table", "active_cell"),
    Input("submissions_table", "data")
)
def pick_submission(active_cell, data):
    if active_cell:
        row = active_cell['row']
        id = data[row]['Student ID']
        return f"Student {id}'s Submission selected", "alert-success", id
    else:
        return "None Selected", "alert-info", ""


# retrieves all submissions of an assignment from the database and returns it in a table
@app.callback(
    Output("download-file", "data"),
    Input("table", "active_cell"),
    Input("table", "data"),
    Input("submissions_table", "active_cell"),
    Input("submissions_table", "data"),
    State('url', 'pathname'),
    Input("btn-download", "n_clicks")
)
def view_submitted_file(activecell, assignmentdata, active_cell, data, url, n_clicks):
    if not n_clicks:
        raise PreventUpdate()
    else:
        lecture = url.strip("prof-lecture/").replace("%20", " ")
        row = activecell['row']
        assignment = assignmentdata[row]['assignment_name']
        if active_cell:
            row = active_cell['row']
            student_id = data[row]['Student ID']
            submitted_file = data[row]['File Submitted']
            directory = f"submitted/{lecture}/{assignment}/{student_id}/{submitted_file}"
            return dcc.send_file(directory)
        else:
            return 0


# Rename columns helper function
def rename_columns(result):
    result = result.rename(columns={
        "assignment_id": "Assignment ID",
        "student_id": "Student ID",
        "submitted_file": "File Submitted",
        "grade": "Grade",
    })
    return result


# retrieves all submissions of an assignment from the database and returns it in a table
@app.callback(
    Output("submissions_table", "children"),
    Input("view-submissions", "n_clicks"),
    Input("assignment_id", "children"),
    Input("table", "active_cell"),
    Input("table", "data")
)
def view_submissions(n_clicks, assignment_id, active_cell, data):
    if not n_clicks:
        raise PreventUpdate()
    else:
        if not active_cell:
            return dbc.Alert("Click on a Row to See Submissions", className="alert-warning")
        else:
            try:
                result = CCDB.get_grades(assignment_id)
                result = rename_columns(result)
            except sqlalchemy.exc.IntegrityError as e:
                pass
            return dbc.Container(
                children=[
                    html.Br(),
                    html.H4("Submissions List"),
                    dash_table.DataTable(id="submissions_table",
                                         data=result.to_dict('records'),
                                         editable=False,
                                         columns=[{"name": i, "id": i} for i in result.columns],
                                         ),
                    dbc.Alert(id="submission_name", className="dark", children="None Selected"),
                    dbc.Button(id="btn-download", children="Download Submitted File"),
                    dcc.Download(id="download-file"),
                    html.Br(),
                    html.Br(),
                    html.Div(id="submission_id", style={'display': 'none'}),
                    dbc.Row([
                        html.Label("Enter Grade (numeric):")
                    ]),
                    dbc.Row([
                        dcc.Input(id="grade-entered"),
                    ]
                    ),
                    dbc.Row([
                        dbc.Button("Grade Assignment", id="grade-assignment"),
                    ],
                        className="md mt-5"
                    ),
                    dbc.Row(id="assignment-graded-status"),

                ],
            )


# parses the contents of an uploaded file
@app.callback(Output('output-image-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              )
def parse_contents(contents, filename):
    return html.Div([
        html.H5(filename),
        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=contents),
        html.Hr(),
    ]
    )


# allows the professor to post an assignment and store it in the database
@app.callback(
    Output("assignment-update-status", "children"),
    State("prof-assignment-name", "value"),
    State("prof-assignment-instructions", "value"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("date", "date"),
    Input("create-assignment", "n_clicks"),
    State("url", "pathname"),
)
def create_assignment(assignment_name, prof_assignment_instructions, content, filename, due_date, n_clicks, url):
    class_name = url.strip("prof-lecture/").replace("%20", " ")
    file_name = filename

    if not n_clicks:
        raise PreventUpdate()
    else:
        if not assignment_name and not (prof_assignment_instructions or file_name):
            return dbc.Alert("Please enter the Assignment Name and its Instructions", className="alert-warning")
        elif not assignment_name:
            return dbc.Alert("Please enter the Assignment Name", className="alert-warning")
        elif not file_name and not prof_assignment_instructions:
            return dbc.Alert("Please enter or upload the instructions", className="alert-warning")
        elif due_date == "Select":
            return dbc.Alert("Please select a Due Date", className="alert-warning")
        else:
            # no uploaded file, but text instructions
            if not file_name:
                file_name = prof_assignment_instructions
            try:
                # create new directory if needed
                assignment = assignment_name.replace(" selected", "")
                directory = f"assignments/{class_name}/{assignment}"
                if not os.path.exists(directory):
                    os.makedirs(directory)

                if content:
                    # Write to file
                    data = content.encode("utf8").split(b";base64,")[1]

                    with open(f"{directory}/{filename}", 'wb') as f:
                        f.write(base64.decodebytes(data))

                result = CCDB.create_assignments(assignment_name, file_name, class_name, due_date)
                print(result)
                # Notify students about the assignment
                # Fetch the assignment ID from the database to do so
                df_asst = CCDB.get_assignments(class_name)
                asst_id = df_asst[df_asst.assignment_name == assignment_name].iloc[0]["assignment_id"]
                send_assignment(asst_id)
                return dbc.Alert("Assignment Created Successfully")
            except sqlalchemy.exc.IntegrityError as e:
                return dbc.Alert(e._message())


# allows the professor to post a grade for each and student and assignment pair in the database
@app.callback(
    Output("assignment-graded-status", "children"),
    State("submissions_table", "data"),
    State("grade-entered", "value"),
    Input("submissions_table", "active_cell"),
    Input("grade-assignment", "n_clicks"),
)
def grade_assignments(data, graded, active_cell, n_clicks):
    if not n_clicks:
        raise PreventUpdate()
    else:
        if active_cell:
            row = active_cell['row']
            assign_id = data[row]['Assignment ID']
            assignment_id = int(assign_id)
            stud_id = data[row]['Student ID']
            student_id = int(stud_id)
            submitted_file = data[row]['File Submitted']
        else:
            return dbc.Alert("You Must Pick a Submission Row to Enter a Grade", className="alert-warning")
        try:
            if not graded:
                return dbc.Alert("Entered Grade Must Be Numeric", className="alert-warning")
            grade = float(graded)
        except ValueError:
            return dbc.Alert("Entered Grade Must Be Numeric", className="alert-warning")

        # make entry in grade table
        CCDB.grade_assignments(assignment_id, student_id, submitted_file, grade)

        # Notify the student that their assignment was graded
        send_grades(assignment_id, student_id)

        return dbc.Alert("Successfully Graded")


# allows a professor to create an announcement and store it in the database
@app.callback(
    Output("announcement-update-status", "children"),
    State("prof-announcement-subject", "value"),
    State("prof-announcement-text", "value"),
    Input("create-announcement", "n_clicks"),
    State("url", "pathname"),
)
def create_announcement(prof_announcement_subject, prof_announcement_text, n_clicks, url):
    if not n_clicks:
        raise PreventUpdate()
    announcements_class_name = url.strip("prof-lecture/").replace("%20", " ")
    if not prof_announcement_subject and not prof_announcement_text:
        return dbc.Alert("Please enter the Announcement Name and its Details", className="alert-warning")
    if not prof_announcement_subject:
        return dbc.Alert("Please enter the Announcement Subject", className="alert-warning")
    if not prof_announcement_text:
        return dbc.Alert("Please enter the Announcement Text", className="alert-warning")
    try:
        CCDB.create_announcement(prof_announcement_subject, prof_announcement_text, announcements_class_name)
        # Notify students about the assignment
        send_announcement(announcements_class_name, prof_announcement_text, prof_announcement_subject)
        return dbc.Alert("Announcement Created Successfully")
    except sqlalchemy.exc.IntegrityError as e:
        return dbc.Alert(e._message())
