import xmltodict
import json
from collections.abc import Mapping
from typing import Union, Any
import math
import datetime


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
        if 'prerequisite_description' in course:
            pass

        # add list of semesters offered to dictionary
        course["semesters_offered"] = []
        if isinstance(course['rotation_term'], list):
            for term in course['rotation_term']:
                course["semesters_offered"].append(term['term'])
        else:
            course["semesters_offered"] = course['rotation_term']['term']

        if 'prerequisite_description' in course:
            course['prerequisite_description'] = course['prerequisite_description']
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
    electives_needed = int(certificate_data[certificate_name]["NoOfElectives"]["num"])

    # add a flag to indicate course was added from the certificate XML
    for course in core_courses:
        core_courses.get(course).update({'certificate': True})
    for course in elective_courses:
        elective_courses.get(course).update({'certificate': True})

    # return finalized dictionary of the course type
    return core_courses, elective_courses, electives_needed


def add_course(current_semester, course_info, current_semester_classes, course, courses_taken,
               total_credits_accumulated, current_semester_credits, course_category):
    # Add course, credits to current semester and list of courses taken, credits earned
    course_added = False
    if current_semester in course_info['semesters_offered']:
        current_semester_classes.append({
            'course': course,
            'name': course_info['course_name'],
            'description': course_info['course_description'],
            'credits': course_info['credit'],
            'category': course_category,
            'prerequisite_description': course_info['prerequisite_description'] if 'prerequisite_description' in course_info.keys() else ''
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


def add_gen_ed_elective() -> dict:
    gen_ed_info = {
        'course': "GEN ED",
        'name': '[User Selects]',
        'description': '',
        'credits': 3,
        'category': "General Education"
    }
    return gen_ed_info


def add_free_elective() -> dict:
    free_elective_info = {
        'course': "FREE",
        'name': '[User Selects]',
        'description': '',
        'credits': 3,
        'category': 'Free Elective'
    }
    return free_elective_info


def create_static_required_courses(required_courses_dict_list):
    required_courses_tuple = []
    for item in required_courses_dict_list:
        required_courses_tuple.append(item[0])
    return tuple(required_courses_tuple)


def print_course_list_information(certificate_core, cert_elective_courses_still_needed,
                                  certificate_electives, min_3000_course_still_needed,
                                  required_courses_tuple):
    print("Certificate Core (Necessary): ")
    for item in certificate_core.keys():
        print(f"\t{item}")
    print(f"Certificate Electives (Pick {cert_elective_courses_still_needed}): ")
    for item in certificate_electives.keys():
        print(f"\t{item}")
    print(f"Min 3000+ Level Electives Still Needed (Above Certificates): {min_3000_course_still_needed}")
    print("Required Course List: ")
    for item in required_courses_tuple:
        if item in certificate_core.keys() and item[0] not in required_courses_tuple:
            print(f"\t{item} ***(Core of Certificate, Now Required)")
        elif item in certificate_electives.keys():
            print(f"\t{item} ***(Elective of Certificate)")
        else:
            print(f"\t{item}")


def intermediate_check_schedule(total_credits_accumulated, required_courses_tuple, courses_taken,
                   min_3000_course_still_needed, cert_elective_courses_still_needed) -> bool:

    # assume that course generation is complete
    is_course_generation_complete = True

    # check that all required core (BSCS and certificate) has been taken
    error_messages = []
    for course in required_courses_tuple:
        if course not in courses_taken:
            error_messages.append(f"ERROR: Must take {course}")
            is_course_generation_complete = False

    # check all required electives have been taken
    if min_3000_course_still_needed != 0:
        is_course_generation_complete = False
        error_messages.append(f"ERROR: Must take {min_3000_course_still_needed} more 3000+ level electives.")

    # check that all certificates have been taken
    if cert_elective_courses_still_needed != 0:
        is_course_generation_complete = False
        error_messages.append(f"ERROR: Must take {cert_elective_courses_still_needed} more certificate electives.")

    # check credit hours
    if total_credits_accumulated < 120:
        is_course_generation_complete = False
        error_messages.append(f"ERROR: Must have 120 credit hours completed. Only {total_credits_accumulated} completed.")

    if is_course_generation_complete == False:
        print(error_messages)

    # check if ultimately finished
    return is_course_generation_complete


def final_check_schedule(total_credits_accumulated, required_courses_tuple, courses_taken,
                   min_3000_course_still_needed, cert_elective_courses_still_needed) -> bool:

    print("\n\nCOURSE CHECK-UP:")
    # assume that course generation is complete
    is_course_generation_complete = True

    # check that all required core (BSCS and certificate) has been taken
    for course in required_courses_tuple:
        if course not in courses_taken:
            print(f"{course:<30}NO")
            is_course_generation_complete = False
        else:
            print(f"{course:<30}YES")

    # check credit hours
    print(f"{'Total credits accumulated:':<30}{total_credits_accumulated:}/{120}")
    if total_credits_accumulated < 120:
        is_course_generation_complete = False

    # check all required electives have been taken
    print(f"{'CMP SCI 3000+ courses needed:':<30}{min_3000_course_still_needed:}")
    if min_3000_course_still_needed != 0:
        is_course_generation_complete = False

    # check that all certificates have been taken
    print(f"{'Certificate courses needed:':<30}{cert_elective_courses_still_needed:}")
    if cert_elective_courses_still_needed != 0:
        is_course_generation_complete = False

    # check if ultimately finished
    print(f"{'Complete?:':<30}{is_course_generation_complete}")

    return is_course_generation_complete


def update_semester(current_semester, include_summer) -> str:
    if current_semester == "Fall":
        return "Spring"
    elif current_semester == "Spring":
        if include_summer:
            return "Summer"
        else:
            return "Fall"
    else:
        return "Fall"


def get_semester_years(selected_season) -> dict:
    # calculate user's current time and season
    seasons_from_month = {
        1: 'Spring',
        2: 'Spring',
        3: 'Spring',
        4: 'Spring',
        5: 'Spring',
        6: 'Summer',
        7: 'Summer',
        8: 'Fall',
        9: 'Fall',
        10: 'Fall',
        11: 'Fall',
        12: 'Fall'
    }
    first_month_of_seasons = {
        'Spring': 1,
        'Summer': 6,
        'Fall': 8
    }
    current_date = datetime.datetime.now()
    current_month = int(current_date.month)
    current_year = int(current_date.year)
    current_season = seasons_from_month[current_month]
    semester_years = {}

    print("Season Information: ")
    print(f"\tCurrent Month: {current_month}")
    print(f"\tCurrent Year: {current_year}")
    print(f"\tCurrent Season: {current_season}")

    # planning for Spring
    if(selected_season == 'Spring'):
        # if in first month of Spring, plan for this Spring
        if (current_month <= first_month_of_seasons[selected_season]):
            print("\tPlan for upcoming Spring")
            semester_years = {
                'Spring': current_year,
                'Summer': current_year,
                'Fall': current_year
            }
        # if NOT in first month of Spring, plan for next Spring
        else:
            print("\tPlan for next Spring")
            semester_years = {
                'Spring': current_year + 1,
                'Summer': current_year + 1,
                'Fall': current_year + 1
            }

    # planning for Fall
    elif(selected_season == 'Fall'):
        # if in first month of Fall, plan for this Fall
        if (current_month <= first_month_of_seasons[selected_season]):
            print("\tPlan for upcoming Fall")
            semester_years = {
                'Spring': current_year + 1,
                'Summer': current_year + 1,
                'Fall': current_year
            }
        # if NOT in first month of Fall, plan for next Fall
        elif (current_month > first_month_of_seasons[selected_season]):
            print("\tPlan for next Fall")
            semester_years = {
                'Spring': current_year + 2,
                'Summer': current_year + 2,
                'Fall': current_year + 1
            }

    elif(selected_season == 'Summer'):
        # if in first month of Summmer, plan for this Summer
        if (current_month <= first_month_of_seasons[selected_season]):
            print("\tPlan for upcoming Summer")
            semester_years = {
                'Spring': current_year + 1,
                'Summer': current_year,
                'Fall': current_year
            }
        # if NOT in first month of Fall, plan for next Fall
        elif (current_month > first_month_of_seasons[selected_season]):
            print("\tPlan for upcoming Summer")
            semester_years = {
                'Spring': current_year + 2,
                'Summer': current_year + 1,
                'Fall': current_year + 1
            }

    print("\t", semester_years)
    print()
    return semester_years


def generate_semester(request): # -> dict[Union[str, Any], Union[Union[str, list, int, list[Any], None], Any]]:
    # get information from user form, routes.py
    course_schedule = json.loads(request.form["course_schedule"])
    current_semester = request.form["current_semester"]
    semester = int(request.form["semester_number"])
    elective_courses = json.loads(request.form["elective_courses"])
    generate_complete_schedule = True if "generate_complete_schedule" in request.form.keys() else False
    num_3000_replaced_by_cert_core = int(request.form["num_3000_replaced_by_cert_core"])  # default is 0
    first_semester = request.form["first_semester"]
    semester_years = json.loads(request.form["semester_years"])

    # credit hour trackers
    total_credits_accumulated = int(request.form["total_credits"])
    free_elective_credits_accumulated = 0
    gen_ed_credits_still_needed = int(request.form["gen_ed_credits_still_needed"])
    cert_elective_courses_still_needed = int(request.form["cert_elective_courses_still_needed"])  # default is 0
    min_3000_course_still_needed = int(request.form["min_3000_course"]) # default is 5

    # set up default variables (also used for counter on scheduling page)
    TOTAL_CREDITS_FOR_GRADUATION = 120
    TOTAL_CREDITS_FOR_BSCS = 71
    TOTAL_CREDITS_FOR_BSCS_ELECTIVES = 15
    TOTAL_CREDITS_FOR_GEN_EDS = 27
    TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES = 0 # set in first semester and maintained by request.form in subsequent semesters
    DEFAULT_CREDIT_HOURS = 3
    course_categories = {
        'R': 'CS Required',
        'E': 'CS Elective',
        'C': 'CS Certificate Elective',
        'G': 'General Education',
        'F': 'Free Elective',
        'O': 'Other'
    }

    # set up scheduler variables, overwritten below
    include_summer = False
    courses_taken = []
    waived_courses = None
    required_courses_dict_list = []

    # set up certificate variables
    # certificate_option = False
    certificate_core = {}
    certificate_electives = {}
    certificate_choice_xml_tag = ""
    certificate_choice_name = ""


    # if the first semester, overwrite schedular variables from above
    if semester == 0:
        first_semester = request.form["current_semester"]
        semester_years = get_semester_years(first_semester)
        print(f"Total Credits Earned Before Semester 1: {total_credits_accumulated}")
        if "include_summer" in request.form.keys():
            include_summer = True if request.form["include_summer"] == "on" else False

        if ("courses_taken" in request.form.keys()):
            courses_taken = request.form.getlist("courses_taken")

        # Do we need separate selects for waived/taken courses or should we combine them to one?
        # If they say taken, do we need to add the credits to the total accumulated credits?
        # ensure waived courses cannot be added when building a semester and remove any duplicates
        if ("waived_courses" in request.form.keys()):
            courses_taken.extend(request.form.getlist("waived_courses"))
            courses_taken = list(dict.fromkeys(courses_taken))

        # if user elects to complete a certificate, get course data for that certificate and decrease electives accordingly
        certificate_choice = request.form["certificate_choice"].split(",")
        certificate_choice_name = certificate_choice[0]
        certificate_choice_xml_tag = certificate_choice[1]

        if (certificate_choice_xml_tag != ""):
            certificate_core, certificate_electives, cert_elective_courses_still_needed = parse_certificate(certificate_choice_xml_tag)
            
            # Update counters according to certificate addition
            min_3000_course_still_needed -= cert_elective_courses_still_needed
            TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES = cert_elective_courses_still_needed * DEFAULT_CREDIT_HOURS
            print(type(cert_elective_courses_still_needed))
            #certificate_option = True

        # determine the semesters that user will be enrolled in
        user_semesters = build_semester_list(current_semester, include_summer)

        # generate required courses
        required_courses_dict = json.loads(request.form['required_courses_dict'])

        # remove University course - INTDSC 1003 - if user has required credits
        if total_credits_accumulated >= 24:
            del required_courses_dict['INTDSC 1003']

        # if a certificate was selected, add the required certificate courses to required courses and update counters
        if certificate_core:
            num_courses_in_base_csdeg = len(required_courses_dict)
            required_courses_dict.update(certificate_core)
            num_3000_replaced_by_cert_core = len(required_courses_dict) - num_courses_in_base_csdeg
            print(f'Number of 3000+ level electives to be used by certificate core: {num_3000_replaced_by_cert_core}')
            
            # update counters according to certificate selection
            min_3000_course_still_needed -= num_3000_replaced_by_cert_core

        for course in courses_taken:
            try:
                del required_courses_dict[course]
            except:
                print(f"Course: {course} was not found in the required_courses_dict")

        # convert required courses dictionary to list for easier processing
        required_courses_dict_list = sorted(list(required_courses_dict.items()), key=lambda d: d[1]["course_number"])
        required_courses_dict_list_unchanged = sorted(list(required_courses_dict.items()), key=lambda d: d[1]["course_number"])

        # holds an immutable tuple of what is required for later comparison (changed into tuple, below)
        required_courses_tuple = create_static_required_courses(required_courses_dict_list)

        # print information for certificates and proposed course schedule, update tuple
        print_course_list_information(certificate_core, cert_elective_courses_still_needed, certificate_electives,
                                      min_3000_course_still_needed, required_courses_tuple)

    # if NOT the first semester
    elif semester != 0:
        required_courses_dict_list = json.loads(request.form['required_courses_dict_list'])
        required_courses_dict_list_unchanged = json.loads(request.form['required_courses_dict_list_unchanged'])
        user_semesters = request.form["semesters"]
        include_summer = True if request.form["include_summer"] == "True" else False

        certificate_choice = json.loads(request.form["certificate_choice"])
        certificate_choice_name = certificate_choice[0]
        certificate_choice_xml_tag = certificate_choice[1]
        TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES = int(request.form["TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES"])

        # courses_taken is returned as a string (that looks like an array), so we have to convert it to a list
        if ("courses_taken" in request.form.keys()):
            courses_taken = request.form["courses_taken"][1:-1]  # removes the '[]' from the string
            courses_taken = courses_taken.replace("'", "")  # removes the string characters around each course
            courses_taken = courses_taken.split(", ")  # creates a list delimited by commas

    # user enters credits for upcoming semester
    min_credits_per_semester = int(request.form["minimum_semester_credits"])
    temp_min_credits_per_semester = min_credits_per_semester

    # adjust credit ratios for scheduling
    max_core_credits_per_semester = math.ceil(min_credits_per_semester * 2/3)
    max_CS_math_total_credits = min_credits_per_semester - 3
    max_CS_elective_credits_per_semester = 6

    # adjust credit parameters for scheduling
    credits_for_3000_level = 60  # 3000+ level credits will not be taken before this many credits earned
    summer_credit_count = int(request.form["minimum_summer_credits"])

    # start with a blank semester
    current_semester_credits = 0
    current_semester_classes = []
    current_semester_cs_math_credits_per_semester = 0
    current_CS_elective_credits_per_semester = 0
    is_course_generation_complete = False

    # create header for console
    if(generate_complete_schedule):
        print(f"Minimum credits for all Fall/Spring semesters: {min_credits_per_semester}")
        print(f"Minimum credits for summer semester: {summer_credit_count}\n\n")
    elif(not generate_complete_schedule):
        print(f"Minimum credits for upcoming semester: {min_credits_per_semester}\n\n")
    print(f"Status:\t{'Num:':<15}{'Course Name:':<40} "
          f"{'Cr of Min:':<5}"
          f"{'Total':>15}/{TOTAL_CREDITS_FOR_GRADUATION}:")

    # loop through to generate a semester or a whole schedule
    while (not is_course_generation_complete):
        course_added = False

        # first, attempt to add a required course
        for index, x in enumerate(required_courses_dict_list):
            course: str = x[0]  # holds course subject + number
            course_info: dict = x[1]  # holds all other information about course
            concurrent = None
            if "concurrent" in course_info.keys():
                concurrent = course_info["concurrent"]

            # add course to schedule if not already added AND current semester doesn't have too many core credits
            if (course not in courses_taken and current_semester_credits < max_core_credits_per_semester):

                # if the course has no pre-requisites
                if len(course_info["prerequisite"]) == 0:
                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits \
                        = add_course(
                        current_semester, course_info, current_semester_classes, course, courses_taken,
                        total_credits_accumulated, current_semester_credits, course_categories['R'])

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
                                        total_credits_accumulated, current_semester_credits, course_categories['R']
                                    )
                                    break

                            # add the current course because pre-requisite has already been taken
                            elif (prereqs in courses_taken) and (
                                    # `not any(current...)` verifies the prereq is not in the current semester class list of dictionaries
                                    (not any(current['course'] == prereqs for current in current_semester_classes)) or (prereqs == concurrent)):
                                required_courses_taken = True
                            else:
                                required_courses_taken = False

                        # if there is a list of pre-requisites
                        else:
                            # if there is only one pre-requisite
                            if (len(prereqs) == 1):

                                # add the current course because pre-requisite has already been taken
                                if (prereqs[0] in courses_taken) and (
                                        (not any(current['course'] == prereqs[0] for current in current_semester_classes))
                                        or (prereqs[0] == concurrent)):
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                                        current_semester, course_info, current_semester_classes, course, courses_taken,
                                        total_credits_accumulated, current_semester_credits, course_categories['R']
                                    )
                                    break

                            # if there is >1 pre-requisite
                            else:
                                required_courses_taken = False

                                # iterate through each pre-requisite
                                for prereq in prereqs:
                                    if (prereq in courses_taken) and (
                                            # `not any(current...)` verifies the prereq is not in the current semester class list of dictionaries
                                            (not any(current['course'] == prereqs for current in current_semester_classes)) or (prereq == concurrent)):
                                        required_courses_taken = True
                                    else:
                                        required_courses_taken = False

                                # add the current course because pre-requisite has already been taken
                                if required_courses_taken:
                                    course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                                        current_semester, course_info, current_semester_classes, course, courses_taken,
                                        total_credits_accumulated, current_semester_credits, course_categories['R']
                                    )
                                    required_courses_taken = False
                                    break
                    if required_courses_taken:
                        course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits = add_course(
                            current_semester, course_info, current_semester_classes, course, courses_taken,
                            total_credits_accumulated, current_semester_credits, course_categories['R']
                        )

                # if the course was added, update semester info
                if course_added:
                    current_semester_cs_math_credits_per_semester += int(course_info['credit'])
                    print(f"Added: \t{course:<15}{course_info['course_name'][:40]:<40} "
                          f"{current_semester_credits:<2} of {min_credits_per_semester:<2}"
                          f"{total_credits_accumulated:>15}")

                    # if generating the whole schedule, complete check to see if graduation requirements are fulfilled
                    if generate_complete_schedule and total_credits_accumulated >= TOTAL_CREDITS_FOR_GRADUATION:
                        print("1st intermediate graduation check...")
                        is_course_generation_complete = intermediate_check_schedule(
                            total_credits_accumulated, required_courses_tuple,
                            courses_taken, min_3000_course_still_needed,
                            cert_elective_courses_still_needed)
                        if is_course_generation_complete:
                            print("1st intermediate graduation check: COMPLETE")
                            is_course_generation_complete = final_check_schedule(total_credits_accumulated, required_courses_tuple,
                            courses_taken, min_3000_course_still_needed,
                            cert_elective_courses_still_needed)
                            current_semester_info = {
                                'semester': current_semester,
                                'semester_number': semester,
                                'credits': current_semester_credits,
                                'schedule': current_semester_classes,
                                'year': semester_years[current_semester]
                            }
                            course_schedule.append(current_semester_info)
                            current_semester_credits = 0
                            current_semester_classes = []
                            semester += 1
                            current_semester_cs_math_credits_per_semester = 0
                            current_CS_elective_credits_per_semester = 0
                            current_semester = update_semester(current_semester, include_summer)
                            break

                    # if credit requirements for semester have been met
                    if current_semester_credits >= min_credits_per_semester:
                        current_semester_info = {
                            'semester': current_semester,
                            'semester_number': semester,
                            'credits': current_semester_credits,
                            'schedule': current_semester_classes,
                            'year': semester_years[current_semester]
                        }
                        course_schedule.append(current_semester_info)

                        # update semester info
                        current_semester_credits = 0
                        current_semester_classes = []
                        semester += 1
                        current_semester_cs_math_credits_per_semester = 0
                        current_CS_elective_credits_per_semester = 0
                        current_semester = update_semester(current_semester, include_summer)
                        if(current_semester == first_semester):
                            semester_years = {key: value + 1 for key, value in semester_years.items()}
                        print(f"\nNext Semester, {current_semester} {semester_years[current_semester]}")

                        # ensure summer credit hours are not F/Sp credit hours
                        if (current_semester == "Summer" and generate_complete_schedule):
                            min_credits_per_semester = summer_credit_count
                        elif (current_semester != "Summer" and generate_complete_schedule):
                            min_credits_per_semester = temp_min_credits_per_semester

                        # if only generating a semester stop here
                        if not generate_complete_schedule:
                            is_course_generation_complete = True

                        # if generating an entire schedule
                        elif generate_complete_schedule and total_credits_accumulated >= TOTAL_CREDITS_FOR_GRADUATION:
                            print("2nd intermediate graduation check...")
                            is_course_generation_complete = intermediate_check_schedule(
                                total_credits_accumulated, required_courses_tuple,
                                courses_taken, min_3000_course_still_needed,
                                cert_elective_courses_still_needed)

                    required_courses_dict_list.pop(index)
                    break

        # second, if a required course was NOT added above, add some kind of elective
        if (not course_added):

            # if user CANNOT take 3000+ level class, due to needing more credit
            if total_credits_accumulated < credits_for_3000_level:
                if gen_ed_credits_still_needed >= DEFAULT_CREDIT_HOURS:
                    current_semester_classes.append(add_gen_ed_elective())
                    gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                    print(f"Added: \t{'GEN ED':<15}{'[User Selects]':<40} "
                          f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                          f"{total_credits_accumulated + 3:>15}")
                else:
                    current_semester_classes.append(add_free_elective())
                    free_elective_credits_accumulated += DEFAULT_CREDIT_HOURS
                    print(f"Added: \t{'FREE ELEC':<15}{'[User Selects]':<40} "
                          f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                          f"{total_credits_accumulated + 3:>15}")

            # if user CAN take 3000+ level classes
            else:
                # user elects for a certificate
                if certificate_choice_xml_tag != "":
                    """
                    check to ensure enough room is in schedule for another CMP SCI class based on 4 conditions:
                        1. The amount of CMP SCI 3000 elective credit is less than pre-determined maximum
                        2. Total credit count of CS/MATH is less than pre-determined maximum 
                        3. There are still CMP SCI 3000 electives to take
                        4. There are still certificate electives to take

                    if all 4 four conditions fail, add a General Education elective or Free Elective
                    """
                    # condition 1 and 2
                    if (current_CS_elective_credits_per_semester <= (max_CS_elective_credits_per_semester - 3)) and \
                            current_semester_cs_math_credits_per_semester <= (max_CS_math_total_credits - 3):
                        # condition 3: if non-elective 3000-level courses are still needed, add these primarily
                        if min_3000_course_still_needed > 0:
                            current_semester_classes.append({
                                    'course': "CMP SCI 3000+",
                                    'name': '[User Selects]',
                                    'description': '',
                                    'credits': 3,
                                    'category': 'CS Elective'
                                })

                            # increment current semester credits, decrement courses needed
                            current_semester_cs_math_credits_per_semester += DEFAULT_CREDIT_HOURS
                            current_CS_elective_credits_per_semester += DEFAULT_CREDIT_HOURS
                            min_3000_course_still_needed -= 1
                            print(f"Added: \t{'COMP SCI 3000+':<15}{'[User Selects]':<40} "
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                                  f"{total_credits_accumulated + 3:>15}")

                        # condition 4: if elective 3000-level courses are still needed, add these secondarily
                        elif cert_elective_courses_still_needed > 0:
                            current_semester_classes.append({
                                    'course': f"CMP SCI {certificate_choice_name} Elective",
                                    'name': '[User Selects]',
                                    'description': '',
                                    'credits': 3,
                                    'category': course_categories['C']
                                })

                            # increment current semester credits, decrement courses needed
                            current_semester_cs_math_credits_per_semester += DEFAULT_CREDIT_HOURS
                            current_CS_elective_credits_per_semester += DEFAULT_CREDIT_HOURS
                            cert_elective_courses_still_needed -= 1
                            print(f"Added: \t{'CMP SCI CERT':<15}{'[User Selects]':<40} "
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                                  f"{total_credits_accumulated + 3:>15}")

                        # all 4 conditions fail.
                        # add a general education elective
                        elif gen_ed_credits_still_needed > 0:
                            current_semester_classes.append(add_gen_ed_elective())
                            print(f"Added: \t{'GEN ED':<15}{'[User Selects]':<40} "
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                                  f"{total_credits_accumulated + 3:>15}")
                            gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                        # add a free elective
                        else:
                            current_semester_classes.append(add_free_elective())
                            free_elective_credits_accumulated += DEFAULT_CREDIT_HOURS
                            print(f"Added: \t{'FREE ELEC':<15}{'[User Selects]':<40} " 
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}" 
                                  f"{total_credits_accumulated + 3:>15}")

                    # if condition 1 or 2 fail, add a type of elective for balance
                    else:
                        if gen_ed_credits_still_needed > 0:
                            current_semester_classes.append(add_gen_ed_elective())
                            gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                            print(f"Added: \t{'GEN ED':<15}{'[User Selects]':<40} "
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                                  f"{total_credits_accumulated + 3:>15}")
                        else:
                            current_semester_classes.append(add_free_elective())
                            free_elective_credits_accumulated += DEFAULT_CREDIT_HOURS
                            print(f"Added: \t{'FREE ELEC':<15}{'[User Selects]':<40} "
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                                  f"{total_credits_accumulated + 3:>15}")


                # user does NOT elect for a certificate
                elif certificate_choice_xml_tag == "":
                    """
                    check to ensure enough room is in schedule for another CMP SCI class based on 3 conditions:
                        1. There are still CMP SCI 3000 electives to take
                        2. The amount of CMP SCI 3000 elective credit is less than pre-determined maximum
                        3. Total credit count of CS/MATH is less than pre-determined maximum 
                    """
                    # condition 1, 2, and 3
                    if min_3000_course_still_needed > 0 and \
                            (current_CS_elective_credits_per_semester <= (max_CS_elective_credits_per_semester - 3)) and \
                            current_semester_cs_math_credits_per_semester <= (max_CS_math_total_credits - 3):
                        current_semester_classes.append({
                            'course': "CMP SCI 3000+",
                            'name': '[User Selects]',
                            'description': '',
                            'credits': 3,
                            'category': course_categories['E']
                        })
                        current_semester_cs_math_credits_per_semester += DEFAULT_CREDIT_HOURS
                        current_CS_elective_credits_per_semester += DEFAULT_CREDIT_HOURS
                        min_3000_course_still_needed -= 1
                        print(f"Added: \t{'CMP SCI 3000+':<15}{'[User Selects]':<40} "
                              f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                              f"{total_credits_accumulated + 3:>15}")

                    # if condition 1, 2, or 3 fail, add a type of elective for balance
                    else:
                        if gen_ed_credits_still_needed > 0:
                            current_semester_classes.append(add_gen_ed_elective())
                            gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                            print(f"Added: \t{'GEN ED':<15}{'[User Selects]':<40} "
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                                  f"{total_credits_accumulated + 3:>15}")
                        else:
                            current_semester_classes.append(add_free_elective())
                            free_elective_credits_accumulated += DEFAULT_CREDIT_HOURS
                            print(f"Added: \t{'FREE ELEC':<15}{'[User Selects]':<40} "
                                  f"{current_semester_credits + 3:<2} of {min_credits_per_semester:<2}"
                                  f"{total_credits_accumulated + 3:>15}")

            # regardless of the type of elective, add the credits
            total_credits_accumulated = total_credits_accumulated + DEFAULT_CREDIT_HOURS
            current_semester_credits = current_semester_credits + DEFAULT_CREDIT_HOURS

            # check if schedule can be suspended now (only for generating whole schedule at once)
            if (total_credits_accumulated > TOTAL_CREDITS_FOR_GRADUATION
                    and generate_complete_schedule
                    and current_semester_credits < min_credits_per_semester):
                print("3rd intermediate graduation check...")
                is_course_generation_complete = intermediate_check_schedule(total_credits_accumulated,
                        required_courses_tuple,
                        courses_taken, min_3000_course_still_needed,
                        cert_elective_courses_still_needed)
                if is_course_generation_complete:
                    print("3rd intermediate graduation check: COMPLETE")
                    is_course_generation_complete = final_check_schedule(
                        total_credits_accumulated, required_courses_tuple,
                        courses_taken, min_3000_course_still_needed,
                        cert_elective_courses_still_needed)

                    current_semester_info = {
                            'semester': current_semester,
                            'semester_number': semester,
                            'credits': current_semester_credits,
                            'schedule': current_semester_classes,
                            'year': semester_years[current_semester]
                        }
                    course_schedule.append(current_semester_info)

            # if the number of credits for the semester has been reached
            if current_semester_credits >= min_credits_per_semester:
                current_semester_info = {
                    'semester': current_semester,
                    'semester_number': semester,
                    'credits': current_semester_credits,
                    'schedule': current_semester_classes,
                    'year': semester_years[current_semester]
                }
                course_schedule.append(current_semester_info)

                # if only generating a semester, stop here
                if not generate_complete_schedule:
                    is_course_generation_complete = True

                # if generating the whole schedule, complete checks
                elif generate_complete_schedule and total_credits_accumulated >= TOTAL_CREDITS_FOR_GRADUATION:
                    print("4th intermediate graduation check...")
                    is_course_generation_complete = intermediate_check_schedule(
                        total_credits_accumulated, required_courses_tuple,
                        courses_taken, min_3000_course_still_needed,
                        cert_elective_courses_still_needed)

                    # if user is ready for graduation, end program
                    if is_course_generation_complete:
                        print("4th intermediate graduation check: COMPLETE")
                        is_course_generation_complete = final_check_schedule(total_credits_accumulated, required_courses_tuple,
                                             courses_taken, min_3000_course_still_needed,
                                             cert_elective_courses_still_needed)
                        current_semester_info = {
                            'semester': current_semester,
                            'semester_number': semester,
                            'credits': current_semester_credits,
                            'schedule': current_semester_classes
                        }

                # update semester info
                current_semester_credits = 0
                current_semester_classes = []
                semester += 1
                current_semester_cs_math_credits_per_semester = 0
                current_CS_elective_credits_per_semester = 0
                current_semester = update_semester(current_semester, include_summer)
                if (current_semester == first_semester):
                    semester_years = {key: value + 1 for key, value in semester_years.items()}
                print(f"\nNext Semester, {current_semester} {semester_years[current_semester]}")

                # ensure summer credit hours are not F/Sp credit hours
                if(current_semester == "Summer" and generate_complete_schedule):
                    min_credits_per_semester = summer_credit_count
                elif (current_semester != "Summer" and generate_complete_schedule):
                    min_credits_per_semester = temp_min_credits_per_semester

    print(f'{certificate_choice=}')
    #print(f'{certificate_option=}')
    print(f'{certificate_choice_xml_tag=}')

    # Calculating counter values (credits for ELECTIVES)
    accumulated_gen_eds = (TOTAL_CREDITS_FOR_GEN_EDS - gen_ed_credits_still_needed)
    accumulated_certificates = (TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES - (cert_elective_courses_still_needed* DEFAULT_CREDIT_HOURS))
    accumulated_3000 = (TOTAL_CREDITS_FOR_BSCS_ELECTIVES - ((min_3000_course_still_needed + cert_elective_courses_still_needed + num_3000_replaced_by_cert_core)*DEFAULT_CREDIT_HOURS))
    ADJUSTED_TOTAL_FOR_3000 = (TOTAL_CREDITS_FOR_BSCS_ELECTIVES - (TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES+ (num_3000_replaced_by_cert_core*DEFAULT_CREDIT_HOURS)))
    adjusted_accumulated_3000 = (ADJUSTED_TOTAL_FOR_3000 -(min_3000_course_still_needed*DEFAULT_CREDIT_HOURS))
    ## print statements were just for troubleshooting, can be removed when counters are all working
    print(f"{min_3000_course_still_needed=} {cert_elective_courses_still_needed=} {num_3000_replaced_by_cert_core=}")
    print(f'TOTAL_CREDITS_FOR_GEN_EDS:               {accumulated_gen_eds:>2} / {TOTAL_CREDITS_FOR_GEN_EDS}')
    print(f'TOTAL_CREDITS_FOR_BSCS_ELECTIVES:        {accumulated_3000:>2} / {TOTAL_CREDITS_FOR_BSCS_ELECTIVES}')
    print(f'TOTAL_CREDITS_FOR_BSCS_ELECTIVES after certificate added: {adjusted_accumulated_3000} / {ADJUSTED_TOTAL_FOR_3000}')
    print(f'TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES: {accumulated_certificates:>2} / {TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES}')
    print(f'Total Free Electives Accumulated:        {free_elective_credits_accumulated:<5}')

    # get course information for generating on HTML
    certificate_courses_remaining = []
    bscs_courses_remaining = []
    for course, info in required_courses_dict_list:
        if 'certificate' in info.keys():
            certificate_courses_remaining.append(course)
        else:
            bscs_courses_remaining.append(course)
            
    print(f'{certificate_courses_remaining=}\n{bscs_courses_remaining=}')
    #print(f'{required_courses_dict_list=}')
    return {
        "free_elective_credits_accumulated": free_elective_credits_accumulated,
        "TOTAL_CREDITS_FOR_GEN_EDS": TOTAL_CREDITS_FOR_GEN_EDS,
        "accumulated_gen_eds": accumulated_gen_eds,
        "TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES": TOTAL_CREDITS_FOR_CERTIFICATE_ELECTIVES,
        "accumulated_certificates": accumulated_certificates,
        "ADJUSTED_TOTAL_FOR_3000": ADJUSTED_TOTAL_FOR_3000,
        "accumulated_3000": adjusted_accumulated_3000,
        "required_courses_dict_list": json.dumps(required_courses_dict_list),
        "required_courses_dict_list_unchanged": json.dumps(required_courses_dict_list_unchanged),
        "semesters": user_semesters,
        "total_credits": total_credits_accumulated,
        "course_schedule": json.dumps(course_schedule),
        "course_schedule_display": course_schedule,
        "courses_taken": courses_taken,
        "semester_number": semester,
        "waived_courses": waived_courses,
        "current_semester": current_semester,
        "minimum_semester_credits": list(map(lambda x: x, range(3, 22))),
        "min_3000_course": min_3000_course_still_needed,
        "include_summer": include_summer,
        "certificate_choice": json.dumps(certificate_choice),
        "num_3000_replaced_by_cert_core": num_3000_replaced_by_cert_core,
        "cert_elective_courses_still_needed": cert_elective_courses_still_needed,
        "saved_minimum_credits_selection": min_credits_per_semester,
        "elective_courses": json.dumps(elective_courses),
        "gen_ed_credits_still_needed": gen_ed_credits_still_needed,
        "full_schedule_generation": generate_complete_schedule,
        "minimum_summer_credits": summer_credit_count,
        "first_semester": first_semester,
        "semester_years": json.dumps(semester_years),
    }
