from flask import render_template, request, json
from app import app
from app.middleware.course_parsing import parse_courses, generate_semester
import pprint

@app.route('/')
@app.route('/index')
def index():
    semesters = ["Fall", "Spring"]
    # create dictionaries for each course type
    core_courses, elective_courses = parse_courses()


    required_courses_list = []
    for course in core_courses.items():
        course_info = {
            "course": course[0],
            "credits": course[1]["credit"],
            "course_number": course[1]["course_number"]
        }
        required_courses_list.append(course_info)

    # sort required courses by course number
    # required_courses_list = sorted(required_courses_list, key=lambda d: d["course_number"])

    return render_template('index.html',
                           initial_load=True,
                           required_courses=required_courses_list,
                           json_required_courses=json.dumps(required_courses_list),
                           required_courses_dict=json.dumps(core_courses),
                           semesters=semesters,
                           total_credits=0,
                           course_schedule=json.dumps([]),
                           elective_courses=json.dumps(elective_courses),
                           include_summer=False,
                           semester_number=0,
                           minimum_semester_credits=list(map(lambda x: x, range(3, 22))), # create list for minimum credits dropdown
                           min_3000_course=5,
                           starting_credits=list(map(lambda x: x, range(0, 201))), # create list for minimum credits dropdown
                           core_credit_count = 0,
    )

@app.route('/schedule', methods=["POST"])
def schedule_generator():
    render_info = generate_semester(request)
    pprint.pprint(render_info["course_schedule_display"])
    return render_template('index.html',
                           required_courses_dict_list=render_info["required_courses_dict_list"],
                           semesters=render_info["semesters"],
                           total_credits=render_info["total_credits"],
                           course_schedule=render_info["course_schedule"],
                           course_schedule_display=render_info["course_schedule_display"],
                           courses_taken=render_info["courses_taken"],
                           semester_number=render_info["semester_number"],
                           waived_courses=render_info["waived_courses"],
                           current_semester=render_info["current_semester"],
                           minimum_semester_credits=render_info["minimum_semester_credits"],
                           min_3000_course=render_info["min_3000_course"],
                           include_summer=render_info["include_summer"],
                           saved_minimum_credits_selection=render_info["saved_minimum_credits_selection"],
                           elective_courses=render_info["elective_courses"]

    )