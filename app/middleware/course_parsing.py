import xmltodict
import json
from collections.abc import Mapping
from typing import Union

def print_dictionary(course_dictionary: dict) -> None:
    """
    prints a dictionary in readable format.

    Parameters
    ----------
    course_dictionary:      dict
                            holds the information for the courses
    Returns
    ----------
    None
    """
    print(json.dumps(course_dictionary, indent=4))


def build_prerequisites(course: dict) -> list:
    """
    creates the list of pre-requisites for a given course.

    Parameters
    ----------
    course:     dict
                holds all information about a particular course, including
                `subject`, `course_number`, etc. (the keys of the dictionary).
    Returns
    ----------
    list
                this will hold either:
                - a single list of courses that are pre-requisites
                - a lists of lists: i.e. multiple lists of possible pre-requisites within a list.
    """
    # creates an empty list to hold any potential pre-requisites
    prereqs_list = []

    # determines if the course has a pre-requisite
    if ('prerequisite' in course.keys()):
        prereqs = course['prerequisite']['or_choice']

        # prerequisite is a dictionary (i.e. one pre-requisite exists)
        if isinstance(prereqs, Mapping):
            prereq = prereqs['and_required']
            if isinstance(prereq, list):
                prereqs_list.append([prereq])
            else:
                prereqs_list.append(prereq)

        # prerequisite is a list of dictionaries (i.e. multiple pre-requisites exist)
        else:
            for prereq in prereqs:
                # Checks if the prerequisite is an array or a comp sci/math class prerequisite
                prereq = prereq['and_required']
                if isinstance(prereq, list):
                    prereqs_list.append(prereq)
                elif (prereq.startswith('CMP SCI') or prereq.startswith('MATH')):
                    prereqs_list.append([prereq])

    # flatten lists of >1 length to keep consistency
    if len(prereqs_list) == 1 and isinstance(prereqs_list[0], list):
        prereqs_list = prereqs_list[0]

    # return a list of pre-requisites
    return prereqs_list


def build_dictionary(courses: Union[dict, list]) -> dict:
    """
    Builds a dictionary with the information for each course included in a course type.

    Course type includes "core courses," "elective courses," etc.

    Parameters
    ----------
    courses:    dict or list
                holds the information for all courses of a certain type (core,
                electives, etc.).

                This parameter is a list of dictionaries if there are multiple courses of a certain type.
                In each dictionary, each key is the XML tag, i.e. `subject`, `course_number`, etc.
                with the corresponding value.

                This parameter is a single dictionary if there is only one course of that type.
                In the dictionary, each key is the XML tag, i.e. `subject`, `course_number`, etc.
                with the corresponding value.

    Returns
    ----------
    dict
                The finalized dictionary of the course type.
                Each key is the course subject and course number.
                The corresponding value is a dictionary holding all the information about that course.
    """
    # create empty dict to store course information
    updated_course_dict = {}

    # Checks if 'courses' is a dictionary
    if isinstance(courses, Mapping):
        courses = [courses]
    for course in courses:
        # add pre-requisites to dictionary
        course['prerequisite'] = build_prerequisites(course)
        key = course["subject"] + " " + course["course_number"]

        # add rest of information to dictionary
        course_dict = {
            key: course
        }

        # add list of semesters offered to dictionary
        course["semesters_offered"] = []
        if isinstance(course['rotation_term'], list):
            for term in course['rotation_term']:
                course["semesters_offered"].append(term['term'])
        else:
            course["semesters_offered"] = course['rotation_term']['term']

        # make final update to course dictionary
        updated_course_dict.update(course_dict)

    # return dictionary with finalized course type dictionary
    return updated_course_dict


def parse_courses() -> dict:
    """
    Parses relevant information from XML and return dictionaries.

    This function opens up the XML file, calls the build_dictionary function
    and returns the dictionary based upon the two parameters provided to
    the function.

    csbs_req is a dictionary that represents a section of parsed XML data. It
    holds each course type as a key and each value for the key is either:
        - a list(if only one course for that key exists) or
        - a dictionary (if multiple courses for that key exist)

    Returns
    ----------
    dict
                    The dictionary that holds all course information
    """
    # open xml document to begin parsing
    with open('app/xml/course_data.xml') as fd:
        doc = xmltodict.parse(fd.read())

    # create a dictionary with course information to further parse
    csbs_req = doc["CSBSReq"]

    core_courses = build_dictionary(csbs_req["CoreCourses"]["course"])
    math_courses = build_dictionary(csbs_req["MathandStatistics"]["course"])
    other_courses = build_dictionary(csbs_req["OtherCourses"]["course"])
    elective_courses = build_dictionary(csbs_req["Electives"]["course"])

    # add math and other courses to core courses so that all BSCS requirements are included
    core_courses.update(math_courses)
    core_courses.update(other_courses)

    # return finalized dictionary of the course type
    return core_courses, elective_courses

def parse_certificate(certificate_name) -> dict:
    """
    Parses relevant information from XML and return dictionaries.

    cscertificate_data.xml is a document that contains all course data for certificates in the computer science program.

    Params
    ----------
    certificate_name        string
                            is the name of the desired certificate. May have any of the following values: 
                            AICERTReq
                            CYBERCERTReq
                            DATACERTReq
                            MOBILECERTReq
                            WEBCERTReq

    Returns
    ----------
    dict

    """
    # open xml document to begin parsing
    with open('app/xml/cscertificate_data.xml') as fd:
        doc = xmltodict.parse(fd.read())

    # create a dictionary with course information to further parse
    certificate_data = doc["CSCertificates"]

    core_courses = build_dictionary(certificate_data[certificate_name]["CertCore"]["course"])
    elective_courses = build_dictionary(certificate_data[certificate_name]["CertElectives"]["course"])

    # return finalized dictionary of the course type
    return core_courses, elective_courses


def add_course(current_semester, course_info, current_semester_classes, course, courses_taken,
               total_credits_accumulated, current_semester_credits):
    # Add course, credits to current semester and list of courses taken, credits earned
    course_added = False
    if current_semester in course_info['semesters_offered']:
        print(course_info)
        current_semester_classes.append({
            'course': course,
            'name': course_info['course_name'],
            'description': course_info['course_description']
        })
        courses_taken.append(course)
        total_credits_accumulated = total_credits_accumulated + int(course_info['credit'])
        current_semester_credits = current_semester_credits + int(course_info['credit'])
        course_added = True
    return course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits


def build_semester_list(first_season="Fall", include_summer=True) -> list:
    possible_semesters = ["Fall", "Spring", "Summer"]

    # Reorder the seasons based on the user's preference for the first season
    first_index = possible_semesters.index(first_season)
    possible_seasons = possible_semesters[first_index:] + possible_semesters[:first_index]

    # Filter out seasons based on user preferences
    selected_semesters = []
    selected_semesters.append("Fall")
    selected_semesters.append("Spring")
    if include_summer:
        selected_semesters.append("Summer")

    if first_season not in selected_semesters:
        return ValueError("First season is not in selected seasons")
    if "Fall" not in selected_semesters or "Spring" not in selected_semesters:
        return ValueError("Fall or Spring must be selected")
    return [season for season in possible_seasons if season in selected_semesters]


def generate_semester(request) -> None:
    # get information from routes.py
    total_credits_accumulated = int(request.form["total_credits"])
    course_schedule = json.loads(request.form["course_schedule"])
    current_semester = request.form["current_semester"]
    semester = int(request.form["semester_number"])
    elective_courses = json.loads(request.form["elective_courses"])
    generate_complete_schedule = True if "generate_complete_schedule" in request.form.keys() else False
    courses_taken = []
    waived_courses = None
    include_summer = False
    min_3000_course = int(request.form["min_3000_course"]) # default is 5
    certificate_choice = request.form["certificate_choice"]
    num_electives_fulfilled_by_cert = int(request.form["num_electives_fulfilled_by_cert"]) # default is 0
    num_electives_in_cert = int(request.form["num_electives_in_cert"]) # default is 0
    certificate_total_courses = 5 # currently true for all certificates, may be better to calculate this number to avoid complications with future changes ...
    certificate_core = {}
    certificate_electives = {}

    # if the first semester, get info about summer, courses taken, and courses waived
    if semester == 0:
        if "include_summer" in request.form.keys():
            include_summer = True if request.form[
                                         "include_summer"] == "on" else False  ## Not sure why it's returning 'on' if checkbox is checked
        if ("courses_taken" in request.form.keys()):
            courses_taken = request.form.getlist("courses_taken")
        ## Do we need separate selects for waived/taken courses or should we combine them to one? If they say taken, do we need to add the credits to the total accumulated credits?
        if ("waived_courses" in request.form.keys()):
            ## Add waived courses to courses_taken list, so they can't be add when building a semester
            courses_taken.extend(request.form.getlist("waived_courses"))
            # Removes duplicates in case a class was added from both waived and taken select options
            courses_taken = list(dict.fromkeys(courses_taken))
        if (certificate_choice != ""):
            ## get the certificate id from the input form and parse course data for that certificate
            certificate_core, certificate_electives = parse_certificate(certificate_choice)
            

        # determine the semesters that user will be enrolled in
        user_semesters = build_semester_list(current_semester, include_summer)

        # generate required courses
        required_courses_dict = json.loads(request.form['required_courses_dict'])

        #if a certificate was selected add the required certificate courses to required courses
        if certificate_core:
            # count how many certificate_core classes will fulfill electives
            num_required_courses = len(required_courses_dict.keys())
            required_courses_dict.update(certificate_core)

            num_electives_fulfilled_by_cert = (len(required_courses_dict.keys()) - num_required_courses)
            num_electives_in_cert = certificate_total_courses - len(certificate_core.keys())

            # update 3000 electives with certificate values
            min_3000_course -= (num_electives_fulfilled_by_cert + num_electives_in_cert)
            
        for course in courses_taken:
            try:
                del required_courses_dict[course]
            except:
                print(f"Course: {course} was not found in the required_courses_dict")
        required_courses_dict_list = sorted(list(required_courses_dict.items()), key=lambda d: d[1]["course_number"])

    # if NOT the first semester
    else:
        required_courses_dict_list = json.loads(request.form['required_courses_dict_list'])
        user_semesters = request.form["semesters"]
        include_summer = True if request.form["include_summer"] == "True" else False
        if ("courses_taken" in request.form.keys()):
            # courses_taken is returned as a string (that looks like an array), so we have to convert it to a list
            courses_taken = request.form["courses_taken"][1:-1]  # this removes the '[]' from the string
            courses_taken = courses_taken.replace("'", "")  # this removes the string characters around each course
            courses_taken = courses_taken.split(
                ", ")  # this creates a list delimited by the ', ' that the courses are separated by

    # user enters credits for upcoming semester
    min_credits_per_semester = int(request.form["minimum_semester_credits"])
    print(f"Minimum credits for this semester: {min_credits_per_semester}")


    ##############################
    ####### Credit amounts #######
    ##############################
    max_core_credits_per_semester = min_credits_per_semester / 2  # sets the total # of credits of core/required classes
    credits_for_3000_level = 60  # 3000+ level credits will not be taken before this many credits earned
    max_CS_elective_credits_per_semester = 6
    max_CS_math_total_credits = min_credits_per_semester - 3
    total_credits_for_degree = 120
    DEFAULT_CREDIT_HOURS = 3

    # start with a blank semester
    current_semester_credits = 0
    current_semester_classes = []
    current_semester_cs_math_credit_count = 0
    is_course_generation_complete = False

    # Loop through to generate a semester or a whole schedule
    while (not is_course_generation_complete):
        current_semester_core_credits = 0
        course_added = False

        # iterate through list of required courses
        for index, x in enumerate(required_courses_dict_list):
            course: str = x[0]  # holds course subject + number
            course_info: dict = x[1]  # holds all other information about course
            concurrent = None
            if "concurrent" in course_info.keys():
                concurrent = course_info["concurrent"]

            # add course to schedule if not already added AND current semester doesn't have too many core credits
            if (course not in courses_taken and
                    current_semester_credits < max_core_credits_per_semester):
                # if the course has no pre-requisites
                if len(course_info["prerequisite"]) == 0:

                    # if course is not ENGLISH 3130, just add iit
                    if (course != "ENGLISH 3130"):
                        course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                            = add_course(
                            current_semester, course_info, current_semester_classes, course, courses_taken,
                            total_credits_accumulated, current_semester_credits)

                    # if course is ENGLISH 3130, add it IF the appropriate credits have been earned
                    if (course == "ENGLISH 3130") and (total_credits_accumulated >= 56) and (prereqs in courses_taken):
                        course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                            = add_course(
                            current_semester, course_info, current_semester_classes, course, courses_taken,
                            total_credits_accumulated, current_semester_credits)

                # if the course has at least one pre-requisite
                else:

                    # look up list of pre-requisites for current course
                    course_added = False
                    prereqs = course_info["prerequisite"]

                    # iterate through pre-requisites for the current course
                    required_courses_taken = False
                    for prereqs in course_info["prerequisite"]:

                        # if there is only one pre-requisite (a string)
                        if isinstance(prereqs, str):

                            # ENGLISH 3130 has a special prerequisite of at least 56 credit hours before the class can be taken
                            if (course == "ENGLISH 3130"):
                                if (total_credits_accumulated >= 56) and (prereqs in courses_taken):
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                                        = add_course(
                                        current_semester, course_info, current_semester_classes, course, courses_taken,
                                        total_credits_accumulated, current_semester_credits
                                    )
                                    break

                            # add the current course because pre-requisite has already been taken
                            elif (prereqs in courses_taken) and (
                                    (prereqs not in current_semester_classes) or (prereqs == concurrent)):
                                required_courses_taken = True
                            else:
                                required_courses_taken = False

                        # if there is a list of pre-requisites
                        else:

                            # if there is only one pre-requisite
                            if (len(prereqs) == 1):

                                # add the current course because pre-requisite has already been taken
                                if (prereqs[0] in courses_taken) and (
                                        (prereqs[0] not in current_semester_classes) or (prereqs[0] == concurrent)):
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                                        current_semester, course_info, current_semester_classes, course, courses_taken,
                                        total_credits_accumulated, current_semester_credits
                                    )
                                    break

                            # if there is >1 pre-requisite
                            else:
                                required_courses_taken = False

                                # iterate through each pre-requisite
                                for prereq in prereqs:
                                    if (prereq in courses_taken) and (
                                            (prereq not in current_semester_classes) or (prereq == concurrent)):
                                        required_courses_taken = True
                                    else:
                                        required_courses_taken = False

                                # add the current course because pre-requisite has already been taken
                                if required_courses_taken:
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                                        current_semester, course_info, current_semester_classes, course, courses_taken,
                                        total_credits_accumulated, current_semester_credits
                                    )
                                    required_courses_taken = False
                                    break
                    if required_courses_taken:
                        course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                            current_semester, course_info, current_semester_classes, course, courses_taken,
                            total_credits_accumulated, current_semester_credits
                        )

                if course_added:
                    current_semester_cs_math_credit_count += int(course_info['credit'])
                    print(f"\t{course} {course_info['course_name']} added, {current_semester_credits}/{min_credits_per_semester}")
                    if current_semester_credits >= min_credits_per_semester:
                        current_semester_info = {
                            'semester': current_semester,
                            'semester number': semester,
                            'credits': current_semester_credits,
                            'schedule': current_semester_classes
                        }
                        course_schedule.append(current_semester_info)

                        # if only generating a semester stop here
                        if not generate_complete_schedule:
                            is_course_generation_complete = True
                        # if generating the whole schedule stop after hitting the 120 credit minimum
                        elif generate_complete_schedule and total_credits_accumulated >= 120:
                            is_course_generation_complete = True

                        # update semester info
                        current_semester_credits = 0
                        current_semester_classes = []
                        semester += 1

                    required_courses_dict_list.pop(index)
                    break

        # if course was not added above, add some kind of elective
        if (not course_added):
            # if in a pre-determined amount of time to NOT take 3000+ level classes, add gen-ed
            if total_credits_accumulated < credits_for_3000_level:
                current_semester_classes.append({
                    'course': "Gen Ed or Elective",
                    'name': '_',
                    'description': ''
                })
                print(f"\tGen Ed or Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")

            # if user can take 3000+ level classes
            else:
                """
                check to ensure enough room is in schedule for another CMP SCI class based on 3 conditions:
                    1. There are still CMP SCI 3000 electives to take
                    2. The amount of CMP SCI 3000 elective credit is less than pre-determined maximum
                    3. Total credit count of CS/MATH is less than pre-determined amount 
                """
                if min_3000_course != 0 and \
                        ((current_semester_classes.count("CMP SCI 3000+ level elective") * DEFAULT_CREDIT_HOURS)
                         < (max_CS_elective_credits_per_semester - 3)) and \
                        current_semester_cs_math_credit_count <= (max_CS_math_total_credits - 3):
                    current_semester_classes.append({
                        'course': "CMP SCI 3000+ level elective",
                        'name': '_',
                        'description': ''
                    })
                    current_semester_cs_math_credit_count += 3
                    print(f"\tCMP SCI 3000+ level elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                    min_3000_course -= 1
                # look closer at this
                elif min_3000_course == 0 and num_electives_in_cert != 0 and \
                        ((current_semester_classes.count("CMP SCI CERTIFICATE elective") * DEFAULT_CREDIT_HOURS)
                         < (max_CS_elective_credits_per_semester - 3)) and \
                        current_semester_cs_math_credit_count <= (max_CS_math_total_credits - 3):
                    current_semester_classes.append({
                        'course': "CMP SCI CERTIFICATE elective",
                        'name': '_',
                        'description': ''
                    })
                    num_electives_in_cert -= 1
                    current_semester_cs_math_credit_count += 3
                    print(f"\tCMP SCI CERTIFICATE elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                # otherwise, add an elective for balance
                else:
                    current_semester_classes.append({
                        'course': "Gen Ed or Elective",
                        'name': '_',
                        'description': ''
                })
                    print(f"\tGen Ed or Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")

            total_credits_accumulated = total_credits_accumulated + 3
            current_semester_credits = current_semester_credits + 3

            if current_semester_credits >= min_credits_per_semester:
                current_semester_info = {
                    'semester': current_semester,
                    'semester number': semester,
                    'credits': current_semester_credits,
                    'schedule': current_semester_classes
                }
                course_schedule.append(current_semester_info)

                # if only generating a semester stop here
                if not generate_complete_schedule:
                    is_course_generation_complete = True
                # if generating the whole schedule stop after hitting the 120 credit minimum
                elif generate_complete_schedule and total_credits_accumulated >= 120:
                    is_course_generation_complete = True

                # update semester info
                current_semester_credits = 0
                current_semester_classes = []
                semester += 1

    # update what the semester is
    if current_semester == "Fall":
        current_semester = "Spring"
    elif current_semester == "Spring":
        if include_summer:
            current_semester = "Summer"
        else:
            current_semester = "Fall"
    else:
        current_semester = "Fall"

    return {
        "required_courses_dict_list": json.dumps(required_courses_dict_list),
        "semesters": user_semesters,
        "total_credits": total_credits_accumulated,
        "course_schedule": json.dumps(course_schedule),
        "course_schedule_display": course_schedule,
        "courses_taken": courses_taken,
        "semester_number": semester,
        "waived_courses": waived_courses,
        "current_semester": current_semester,
        "minimum_semester_credits": list(map(lambda x: x, range(3, 22))),
        "min_3000_course": min_3000_course,
        "include_summer": include_summer,
        "certificate_choice": certificate_choice,
        "num_electives_fulfilled_by_cert": num_electives_fulfilled_by_cert,
        "num_electives_in_cert": num_electives_in_cert,
        "saved_minimum_credits_selection": min_credits_per_semester,
        "elective_courses": json.dumps(elective_courses),
    }
