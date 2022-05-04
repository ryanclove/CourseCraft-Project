import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from web.app import login, prof_lecture, not_found, lecture, create_account, dean, student, professor
from web.app.ccapp import app

# App layout wrapper, which also stores session data.
app.layout = html.Div(
    [
        dcc.Store(id="session-account"),
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content")
    ]
)


# setup up all routes to redirect users to different pages
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == "/" or pathname == "/login":
        return login.layout
    elif pathname == "/create_account":
        return create_account.layout
    elif pathname == "/dean":
        return dean.layout
    elif pathname == "/student":
        return student.layout
    elif pathname == "/course_registration":
        return student.registration_layout
    elif pathname == "/view_schedule":
        return student.view_schedule_layout
    elif pathname == "/professor":
        return professor.layout
    elif pathname == "/create_course":
        return dean.create_course_layout
    elif pathname == "/register_to_teach":
        return professor.register_layout
    elif pathname.__contains__("/lecture"):
        return lecture.layout
    elif pathname.__contains__("/prof-lecture"):
        return prof_lecture.layout
    elif pathname == "/generate_future_gpa":
        return student.calculate_future_gpa_layout
    elif pathname == "/generate_semester_gpa":
        return student.calculate_semester_gpa_layout
    else:
        return not_found.layout


if __name__ == "__main__":
    app.run_server(debug=True)
