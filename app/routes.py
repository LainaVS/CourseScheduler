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
                           required_courses_dict_list=json.dumps(required_courses_dict_list),
                           semesters=semesters,
                           total_credits=0,
                           course_schedule=json.dumps([]),
                           elective_course=json.dumps(elective_courses),
                           include_summer=False,
                           semester_number=0,
                           minimum_semester_credits=list(map(lambda x: x, range(3, 121))), # create list for minimum credits dropdown
                           min_3000_course=5
    )

@app.route('/schedule', methods=["POST"])
def schedule_generator():
    required_courses_dict_list = json.loads(request.form['required_courses_dict_list'])
    total_credits_accumulated = int(request.form["total_credits"])
    course_schedule = json.loads(request.form["course_schedule"])

    current_semester = request.form["current_semester"]
    semester = int(request.form["semester_number"])

    waived_courses = None
    courses_taken = []

    if ("waived_courses" in request.form.keys()):
        waived_courses = request.form["waived_courses"]
    if ("courses_taken" in request.form.keys()):
        courses_taken = json.loads(request.form["courses_taken"])

    include_summer = False

    if len(courses_taken) == 0:
        user_semesters = build_semester_list(current_semester, include_summer)
        if "include_summer" in request.form.keys():
            include_summer = True
    else:
        user_semesters = request.form["semesters"]
        include_summer = request.form["include_summer"]

    min_credits_per_semester = int(request.form["minimum_semester_credits"])
    min_3000_course = int(request.form["min_3000_course"])

    current_semester_credits = 0
    current_semester_classes = []

    is_semester_complete = False

    while (not is_semester_complete):
        course_added = False
        # iterate through list of required courses
        for index, x in enumerate(required_courses_dict_list):
            course: str = x[0]                      # holds course subject + number
            course_info: dict = x[1]                # holds all other information about course
            concurrent = None
            if "concurrent" in course_info.keys():
                concurrent = course_info["concurrent"]

            # add course to schedule if it has not already been added
            if (course not in courses_taken):

                # if the course has no pre-requisites, add current course to schedule
                if len(course_info["prerequisite"]) == 0:
                    if (course != "ENGLISH 3130"):
                        course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                        = add_course(
                        current_semester, course_info, current_semester_classes, course, courses_taken, total_credits_accumulated, current_semester_credits)
                    if (course == "ENGLISH 3130") and (total_credits_accumulated >= 56) and (prereqs in courses_taken):
                        course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                        = add_course(
                        current_semester, course_info, current_semester_classes, course, courses_taken, total_credits_accumulated, current_semester_credits)
                # if the course has at least one pre-requisite
                else:
                    # look up list of pre-requisites for current course
                    course_added = False
                    prereqs = course_info["prerequisite"]

                    # iterate through pre-requisites for the current course
                    for prereqs in course_info["prerequisite"]:
                        # if there is only one pre-requisite (a string)
                        if isinstance(prereqs, str):
                            # ENGLISH 3130 has a special prerequisite of at least 56 credit hours before the class can be taken
                            if (course == "ENGLISH 3130"):
                                if (total_credits_accumulated >= 56) and (prereqs in courses_taken):
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                                    = add_course(
                                    current_semester, course_info, current_semester_classes, course, courses_taken, total_credits_accumulated, current_semester_credits
                                    )
                                    break
                            # add the current course because pre-requisite has already been taken
                            elif (prereqs in courses_taken) and ((prereqs not in current_semester_classes) or (prereqs == concurrent)):
                                course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                                = add_course(
                                current_semester, course_info, current_semester_classes, course, courses_taken, total_credits_accumulated, current_semester_credits
                                )
                                break

                        # if there is a list of pre-requisites
                        else:
                            # if there is only one pre-requisite
                            if (len(prereqs) == 1):
                                # add the current course because pre-requisite has already been taken
                                if (prereqs[0] in courses_taken) and ((prereqs[0] not in current_semester_classes) or (prereqs[0] == concurrent)):
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                                        current_semester, course_info, current_semester_classes, course, courses_taken, total_credits_accumulated, current_semester_credits
                                    )
                                    break

                            # if there is >1 pre-requisite
                            else:
                                required_courses_taken = False
                                # iterate through each pre-requisite
                                for prereq in prereqs:
                                    if (prereq in courses_taken) and ((prereq not in current_semester_classes) or (prereq == concurrent)):
                                        required_courses_taken = True
                                    else:
                                        required_courses_taken = False
                                # add the current course because pre-requisite has already been taken
                                if required_courses_taken:
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                                        current_semester, course_info, current_semester_classes, course, courses_taken, total_credits_accumulated, current_semester_credits
                                    )
                                    break

                if course_added:
                    if total_credits_accumulated >= 120:
                        current_semester_info = {
                            'semester': current_semester,
                            'semester number': semester,
                            'credits': current_semester_credits,
                            'schedule': current_semester_classes
                        }
                        course_schedule.append(current_semester_info)
                        is_semester_complete = True
                    elif current_semester_credits >= min_credits_per_semester:
                        current_semester_info = {
                            'semester': current_semester,
                            'semester number': semester,
                            'credits': current_semester_credits,
                            'schedule': current_semester_classes
                        }
                        course_schedule.append(current_semester_info)
                        is_semester_complete = True

                        # update semester info
                        current_semester_credits = 0
                        current_semester_classes = []
                        semester += 1
                    required_courses_dict_list.pop(index)
                    break
        if (not course_added):
            if total_credits_accumulated > 80 and min_3000_course != 0:
                current_semester_classes.append("CMP SCI 3000+ level elective")
                min_3000_course = min_3000_course - 1
            else:
                current_semester_classes.append("Gen Ed or Elective")
            total_credits_accumulated = total_credits_accumulated + 3
            current_semester_credits = current_semester_credits + 3

            if total_credits_accumulated >= 120:
                current_semester_info = {
                    'semester': current_semester,
                    'semester number': semester,
                    'credits': current_semester_credits,
                    'schedule': current_semester_classes
                }
                course_schedule.append(current_semester_info)
                is_semester_complete = True
            elif current_semester_credits >= min_credits_per_semester:
                current_semester_info = {
                    'semester': current_semester,
                    'semester number': semester,
                    'credits': current_semester_credits,
                    'schedule': current_semester_classes
                }
                course_schedule.append(current_semester_info)
                is_semester_complete = True

                # update semester info
                current_semester_credits = 0
                current_semester_classes = []
                semester += 1

    if current_semester == "Fall":
        current_semester = "Spring"
    elif current_semester == "Spring":
        if include_summer:
            current_semester = "Summer"
        else:
            current_semester = "Fall"
    else:
        current_semester = "Fall"

    return render_template('index.html',
                           required_courses_dict_list=json.dumps(required_courses_dict_list),
                           semesters=user_semesters,
                           total_credits=total_credits_accumulated,
                           course_schedule=json.dumps(course_schedule),
                           course_schedule_display=course_schedule,
                           courses_taken=json.dumps(courses_taken),
                           semester_number=semester,
                           waived_courses=waived_courses,
                           current_semester=current_semester,
                           minimum_semester_credits=list(map(lambda x: x, range(3, 121))),
                           min_3000_course=min_3000_course,
                           include_summer=include_summer
    )