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
                           user_name = "Student",
                           ge_taken = 0,
                           fe_taken = 0,
                           is_graduated = False,
                           required_courses_tuple = json.dumps([]),
                           number_of_required_courses_taken = 0,
                           list_of_required_courses_taken = json.dumps([]),
                           certificate_choice = json.dumps([])
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
                           certificates_display = render_info["certificates_display"],
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
                           semester_years_display = render_info["semester_years_display"],
                           course_prereqs_for = render_info['course_prereqs_for'],
                           user_name = render_info['user_name'],
                           ge_taken = render_info['ge_taken'],
                           fe_taken = render_info['fe_taken'],
                           is_graduated = render_info['is_graduated'],
                           required_courses_tuple = render_info['required_courses_tuple'],
                           number_of_required_courses_taken = render_info['number_of_required_courses_taken'],
                           list_of_required_courses_taken = render_info['list_of_required_courses_taken'],
                           required_courses_tuple_display = render_info["required_courses_tuple_display"],
                           list_of_required_courses_taken_display = render_info["list_of_required_courses_taken_display"]
    )

@app.route('/printable')
def printable():
    course_schedule_display_json = request.args.get('course_schedule_display', None)
    total_credits = request.args.get('total_credits', None)
    certificate_choice = request.args.get('certificate_choice', None)
    gen_ed_credits_still_needed = request.args.get('gen_ed_credits_still_needed', None)
    user_name = request.args.get('user_name', None)
    fe_taken = request.args.get('fe_taken', None)
    min_3000_course = request.args.get('min_3000_course', None)
    num_3000_replaced_by_cert_core = request.args.get('num_3000_replaced_by_cert_core', None)
    cert_elective_courses_still_needed = request.args.get('cert_elective_courses_still_needed', None)
    TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES = request.args.get('TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES', None)
    if course_schedule_display_json:
        course_schedule_display = json.loads(course_schedule_display_json)
        print("Course Schedule Display:")
        print(course_schedule_display)
    else:
        course_schedule_display = None

    return render_template('printable.html',
                           course_schedule_display=course_schedule_display,
                            total_credits = total_credits,
                            certificate_choice = certificate_choice,
                            gen_ed_credits_still_needed = int(gen_ed_credits_still_needed),
                            user_name = user_name,
                            fe_taken = fe_taken,
                            min_3000_course = min_3000_course,
                            num_3000_replaced_by_cert_core = num_3000_replaced_by_cert_core,
                            cert_elective_courses_still_needed = cert_elective_courses_still_needed,
                            TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES = TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES
    )