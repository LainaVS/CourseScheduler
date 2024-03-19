from flask import render_template, request, json
from app import app
from app.course_parsing import parse_courses, add_course, build_semester_list

@app.route('/')
@app.route('/index')
def index():
    semesters = ["Fall", "Spring", "Summer"]
    # create dictionaries for each course type
    core_courses, elective_courses = parse_courses()

    # sort required courses by course number
    required_courses_list = sorted(list(core_courses.keys()))
    required_courses_dict_list = sorted(list(core_courses.items()), key=lambda d: d[1]["course_number"])
    return render_template('index.html',
                           initial_load=True,
                           required_courses=required_courses_list,
                           required_courses_dict_list=required_courses_dict_list,
                           semesters=semesters,
                           total_credits=0,
                           course_schedule=[],
                           elective_course=elective_courses,
                           include_summer=False,
                           semester_number=0
    )

@app.route('/schedule', methods=["POST"])
def schedule_generator():
    semesters = ["Fall", "Spring", "Summer"]
    # create dictionaries for each course type
    core_courses, elective_courses = parse_courses()

    # sort required courses by course number
    required_courses_list = sorted(list(core_courses.keys()))
    required_courses_dict_list = sorted(list(core_courses.items()), key=lambda d: d[1]["course_number"])
    return render_template('index.html',
                           required_courses=required_courses_list,
                           required_courses_dict_list=required_courses_dict_list,
                           semesters=semesters,
                           total_credits=0,
                           course_schedule=[],
                           elective_course=elective_courses,
                           include_summer=False,
                           semester_number=0
    )