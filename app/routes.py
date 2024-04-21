from flask import render_template, request, json
from app import app
from app.middleware.course_parsing import parse_courses, generate_semester

@app.route('/')
@app.route('/index')
def index():
    semesters = ["Fall", "Spring"]
    certificates = [("None", ""), ("Artificial Intelligence", "AICERTReq"), ("Cybersecurity", "CYBERCERTReq"), ("Data Science", "DATACERTReq"), ("Mobile Apps and Computing", "MOBILECERTReq"), ("Internet and Web", "WEBCERTReq")]
    #num_3000_replaced_by_cert_core=0
    #cert_elective_courses_still_needed=0
    # create dictionaries for each course type
    core_courses, elective_courses = parse_courses()

    required_courses_list = []
    for course in core_courses.items():
        course_info = {
            "course": course[0],
            "credits": course[1]["credit"],
            "course_number": course[1]["course_number"],
            "prerequisite_description": course[1]["prerequisite_description"]
        }
        required_courses_list.append(course_info)
    # sort required courses by course number
    # required_courses_list = sorted(required_courses_list, key=lambda d: d["course_number"])
    # required_courses_list = sorted(list(core_courses.keys()))

    return render_template('index.html',
                           initial_load=True,
                           required_courses=required_courses_list,
                           required_courses_dict=json.dumps(core_courses),
                           json_required_courses=json.dumps(required_courses_list),
                           semesters=semesters,
                           certificates=certificates,
                           num_3000_replaced_by_cert_core=0,
                           cert_elective_courses_still_needed=0,
                           total_credits=0,
                           course_schedule=json.dumps([]),
                           elective_courses=json.dumps(elective_courses),
                           include_summer=False,
                           semester_number=0,
                           minimum_semester_credits=list(map(lambda x: x, range(3, 22))), # create list for minimum credits dropdown
                           min_3000_course=5,
                           starting_credits=list(map(lambda x: x, range(0, 201))), # create list for minimum credits dropdown
                           core_credit_count = 0,
                           gen_ed_credits_still_needed=27,
                           minimum_summer_credits = list(map(lambda x: x, range(0, 10))),
                           semester_years = json.dumps({}),
                           user_name = "test"
    )

@app.route('/schedule', methods=["POST"])
def schedule_generator():
    render_info = generate_semester(request)
    return render_template('index.html',
                           required_courses_dict_list=render_info["required_courses_dict_list"],
                           required_courses_dict_list_unchanged=render_info["required_courses_dict_list_unchanged"],
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
                           certificates=render_info["certificate_choice"],
                           num_3000_replaced_by_cert_core=render_info["num_3000_replaced_by_cert_core"],
                           cert_elective_courses_still_needed=render_info["cert_elective_courses_still_needed"],
                           TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES=render_info["TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES"],
                           saved_minimum_credits_selection=render_info["saved_minimum_credits_selection"],
                           elective_courses=render_info["elective_courses"],
                           gen_ed_credits_still_needed=render_info['gen_ed_credits_still_needed'],
                           full_schedule_generation=render_info['full_schedule_generation'],
                           minimum_summer_credits=render_info['minimum_summer_credits'],
                           first_semester = render_info['first_semester'],
                           semester_years = render_info['semester_years'],
                           course_prereqs_for = render_info['course_prereqs_for'],
                           user_name = render_info['user_name']
    )