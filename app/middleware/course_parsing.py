import xmltodict
import json
from collections.abc import Mapping
from typing import Union, Dict, Any, List
from pprint import pprint


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
    electives_needed = int(certificate_data[certificate_name]["NoOfElectives"]["num"])

    # return finalized dictionary of the course type
    return core_courses, elective_courses, electives_needed


def add_course(current_semester, course_info, current_semester_classes, course, courses_taken,
               total_credits_accumulated, current_semester_credits):
    # Add course, credits to current semester and list of courses taken, credits earned
    course_added = False
    if current_semester in course_info['semesters_offered']:
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


def add_gen_ed_elective() -> dict:
    gen_ed_info = {
        'course': "General Education Elective",
        'name': '_',
        'description': ''
    }
    return gen_ed_info


def add_free_elective() -> dict:
    free_elective_info = {
        'course': "Free Elective",
        'name': '_',
        'description': ''
    }
    return free_elective_info


def create_static_required_courses(required_courses_dict_list):
    required_courses_tuple = []
    for item in required_courses_dict_list:
        required_courses_tuple.append(item[0])
    return tuple(required_courses_tuple)


def print_course_list_information(certificate_core, cert_electives_still_needed,
                                  certificate_electives,
                                  min_3000_course_still_needed,
                                  required_courses_tuple):
    print("Certificate Core (Necessary): ")
    for item in certificate_core.keys():
        print(f"\t{item}")
    print(f"Certificate Electives (Pick {cert_electives_still_needed}): ")
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

def generate_semester(request) -> dict[Union[str, Any], Union[Union[str, list, int, list[Any], None], Any]]:
    # get information from user form, routes.py
    total_credits_accumulated = int(request.form["total_credits"])
    course_schedule = json.loads(request.form["course_schedule"])
    current_semester = request.form["current_semester"]
    semester = int(request.form["semester_number"])
    elective_courses = json.loads(request.form["elective_courses"])
    generate_complete_schedule = True if "generate_complete_schedule" in request.form.keys() else False
    cert_electives_still_needed = int(request.form["cert_electives_still_needed"])  # default is 0
    min_3000_course_still_needed = int(request.form["min_3000_course"]) # default is 5
    certificate_choice = request.form["certificate_choice"]
    num_3000_replaced_by_cert_core = int(request.form["num_3000_replaced_by_cert_core"])  # default is 0

    # # # # # # # # # # # # # # # # # # # # # # # #
    # These are new variables, double-check them #
    # # # # # # # # # # # # # # # # # # # # # # # #
    TOTAL_CREDITS_FOR_GRADUATION = 120
    TOTAL_CREDITS_FOR_BSCS = 71
    DEFAULT_CREDIT_HOURS = 3
    DEFAULT_GEN_ED_CREDITS = 27
    free_elective_credits_still_needed = TOTAL_CREDITS_FOR_GRADUATION - TOTAL_CREDITS_FOR_BSCS - DEFAULT_GEN_ED_CREDITS
    gen_ed_credits_still_needed = DEFAULT_GEN_ED_CREDITS

    # set up scheduler variables, overwritten below
    include_summer = False
    courses_taken = []
    waived_courses = None

    # set up certificate variables
    certificate_core = {}
    certificate_electives = {}
    certificate_option = False

    # if the first semester, overwrite scheduler variables from above
    if semester == 0:
        if "include_summer" in request.form.keys():
            # 'on' is when the checkbox is checked
            include_summer = True if request.form["include_summer"] == "on" else False

        if ("courses_taken" in request.form.keys()):
            courses_taken = request.form.getlist("courses_taken")

        ## Do we need separate selects for waived/taken courses or should we combine them to one? If they say taken, do we need to add the credits to the total accumulated credits?
        if ("waived_courses" in request.form.keys()):
            ## add waived courses to courses_taken list, so they cannot be add when building a semester
            courses_taken.extend(request.form.getlist("waived_courses"))

            # demoves duplicates in case a class was added from both waived and taken select options
            courses_taken = list(dict.fromkeys(courses_taken))

        if (certificate_choice != ""):
            ## get the certificate id from the input form and parse course data for that certificate
            certificate_core, certificate_electives, cert_electives_still_needed = parse_certificate(certificate_choice)

            # decrease min_3000 electives, based on how many certificate specific electives are required.
            min_3000_course_still_needed -= cert_electives_still_needed
            certificate_option = True

        # determine the semesters that user will be enrolled in
        user_semesters = build_semester_list(current_semester, include_summer)

        # generate required courses
        required_courses_dict = json.loads(request.form['required_courses_dict'])

        # if a certificate was selected, add the required certificate courses to required courses
        if certificate_core:
            # count classes in base degree before adding certificate requirements
            num_courses_in_base_csdeg = len(required_courses_dict)

            # update base degree to include certificate requirements
            # certificate course dictionary keys are identical to keys in required_courses_dict so if a certificate requirement is already a base degree requirement, required_courses_dict (size) will not change.
            required_courses_dict.update(certificate_core)

            # count how many new courses were actually added to base degree, each new course will replace a 3000+ elective
            num_3000_replaced_by_cert_core = (len(required_courses_dict) - num_courses_in_base_csdeg)
            print(f'Number of 3000+ level electives to be used by certificate core: {num_3000_replaced_by_cert_core}')

            # decrease min_3000 electives again, based on how many certificate core classes double as electives.
            min_3000_course_still_needed -= num_3000_replaced_by_cert_core

        for course in courses_taken:
            try:
                del required_courses_dict[course]
            except:
                print(f"Course: {course} was not found in the required_courses_dict")

        # convert required courses dictionary to list for easier processing
        required_courses_dict_list = sorted(list(required_courses_dict.items()), key=lambda d: d[1]["course_number"])

        # holds an immutable tuple of what is required for later comparison (changed into tuple, below)
        required_courses_tuple = create_static_required_courses(required_courses_dict_list)

        # print information for certificates and proposed course schedule, update tuple
        print_course_list_information(certificate_core, cert_electives_still_needed,
                                          certificate_electives,
                                          min_3000_course_still_needed,
                                          required_courses_tuple)

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
    print(f"Minimum credits for all Fall/Spring semesters: {min_credits_per_semester}")

    # adjust credit ratios for scheduling parameters
    max_core_credits_per_semester = (min_credits_per_semester / 2)  # sets the total # of credits of core/required classes
    credits_for_3000_level = 60  # 3000+ level credits will not be taken before this many credits earned
    max_CS_elective_credits_per_semester = 6
    max_CS_math_total_credits = min_credits_per_semester - 3

    # start with a blank semester
    current_semester_credits = 0
    current_semester_classes = []
    current_semester_cs_math_credits_per_semester = 0
    current_CS_elective_credits_per_semester = 0
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
            if (course not in courses_taken and current_semester_credits < max_core_credits_per_semester):

                # if the course has no pre-requisites
                if len(course_info["prerequisite"]) == 0:

                    # if course is not ENGLISH 3130, just add it
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
                                            # `not any(current...)` verifies the prereq is not in the current semester class list of dictionaries
                                            (not any(current['course'] == prereqs for current in current_semester_classes)) or (prereq == concurrent)):
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

                # if the course was added, update semester info
                if course_added:
                    current_semester_cs_math_credits_per_semester += int(course_info['credit'])
                    print(f"\t{course} {course_info['course_name']} added, {current_semester_credits}/{min_credits_per_semester}")
                    if current_semester_credits >= min_credits_per_semester:
                        current_semester_info = {
                            'semester': current_semester,
                            'semester number': semester,
                            'credits': current_semester_credits,
                            'schedule': current_semester_classes
                        }
                        course_schedule.append(current_semester_info)

                        # update semester info
                        current_semester_credits = 0
                        current_semester_classes = []
                        semester += 1
                        current_semester_cs_math_credits_per_semester = 0
                        current_CS_elective_credits_per_semester = 0
                        if current_semester == "Fall":
                            current_semester = "Spring"
                        elif current_semester == "Spring":
                            if include_summer:
                                current_semester = "Summer"
                            else:
                                current_semester = "Fall"
                        else:
                            current_semester = "Fall"
                        print("Next Semester: ")

                        # if only generating a semester stop here
                        if not generate_complete_schedule:
                            is_course_generation_complete = True

                        # if generating the whole schedule stop after hitting the 120 credit minimum
                        #############################################################################
                        ###### MIGHT WANT TO CHANGE THIS: NEEDS MORE REQUIREMENTS THAN JUST 120 #####
                        #############################################################################
                        elif generate_complete_schedule and total_credits_accumulated >= 120:
                            is_course_generation_complete = True

                    required_courses_dict_list.pop(index)
                    break

        # if course was NOT added above, add some kind of elective
        if (not course_added):

            # if user CANNOT take 3000+ level class, due to needing more credit
            if total_credits_accumulated < credits_for_3000_level:
                if (gen_ed_credits_still_needed >= DEFAULT_CREDIT_HOURS):
                    current_semester_classes.append(add_gen_ed_elective())
                    print(f"\tGeneral Education Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                    gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                else:
                    current_semester_classes.append(add_free_elective())
                    print(f"\tFree Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                    free_elective_credits_still_needed -= DEFAULT_CREDIT_HOURS

            # if user CAN take 3000+ level classes
            else:
                # user elects for a certificate
                if certificate_option == True:
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
                                        'course': "CMP SCI 3000+ level elective",
                                        'name': '_',
                                        'description': ''
                                    })
                                # increment current semester credits, decrement courses needed
                                current_semester_cs_math_credits_per_semester += 3
                                current_CS_elective_credits_per_semester += 3
                                min_3000_course_still_needed -= 1
                                print(f"\tCMP SCI 3000+ level elective added, {current_semester_credits + 3}/{min_credits_per_semester}")

                            # condition 4: if elective 3000-level courses are still needed, add these secondarily
                            elif cert_electives_still_needed > 0:
                                current_semester_classes.append({
                                        'course': "CMP SCI certificate elective",
                                        'name': '_',
                                        'description': ''
                                    })
                                # increment current semester credits, decrement courses needed
                                current_semester_cs_math_credits_per_semester += 3
                                current_CS_elective_credits_per_semester += 3
                                cert_electives_still_needed -= 1
                                print(f"\tCMP SCI certificate elective added, {current_semester_credits + 3}/{min_credits_per_semester}")

                            # all 4 conditions fail. Add an elective.
                            if (gen_ed_credits_still_needed > 0):
                                current_semester_classes.append(add_gen_ed_elective())
                                print(
                                    f"\tGeneral Education Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                                gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                            else:
                                current_semester_classes.append(add_free_elective())
                                print(
                                    f"\tFree Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                                free_elective_credits_still_needed -= DEFAULT_CREDIT_HOURS

                    # otherwise, add a type of elective for balance
                    else:
                        if (gen_ed_credits_still_needed > 0):
                            current_semester_classes.append(add_gen_ed_elective())
                            print(f"\tGeneral Education Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                            gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                        else:
                            current_semester_classes.append(add_free_elective())
                            print(f"\tFree Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                            free_elective_credits_still_needed -= DEFAULT_CREDIT_HOURS

                # user does NOT elect for a certificate
                elif certificate_option == False:
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
                            'course': "CMP SCI 3000+ level elective",
                            'name': '_',
                            'description': ''
                        })
                        current_semester_cs_math_credits_per_semester += 3
                        current_CS_elective_credits_per_semester += 3
                        min_3000_course_still_needed -= 1
                        print(f"\tCMP SCI 3000+ level elective added, {current_semester_credits + 3}/{min_credits_per_semester}")

                    # otherwise, add a type of elective for balance
                    else:
                        if (gen_ed_credits_still_needed > 0):
                            current_semester_classes.append(add_gen_ed_elective())
                            print(
                                f"\tGeneral Education Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                            gen_ed_credits_still_needed -= DEFAULT_CREDIT_HOURS
                        else:
                            current_semester_classes.append(add_free_elective())
                            print(f"\tFree Elective added, {current_semester_credits + 3}/{min_credits_per_semester}")
                            free_elective_credits_still_needed -= DEFAULT_CREDIT_HOURS

            # regardless of what type of elective is added, add credit hours
            total_credits_accumulated = total_credits_accumulated + DEFAULT_CREDIT_HOURS
            current_semester_credits = current_semester_credits + DEFAULT_CREDIT_HOURS

            # if the number of credits for the semester has been reached
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
                elif generate_complete_schedule and total_credits_accumulated >= TOTAL_CREDITS_FOR_GRADUATION:
                    # assume that schedule generation is finished
                    is_course_generation_complete = True

                    # check that all required courses has been taken
                    print("CHECKING COURSE REQUIREMENTS")
                    for course in required_courses_tuple:
                        if course not in courses_taken:
                            print(f"\t{course} (NOT TAKEN)")
                            is_course_generation_complete = False
                        else:
                            print(f"\t{course}")

                    # check all required electives have been taken
                    print(f"CMP SCI 3000+ courses needed: {min_3000_course_still_needed}")
                    if min_3000_course_still_needed != 0:
                        is_course_generation_complete = False

                    print(f"Certicate courses needed: {min_3000_course_still_needed}")
                    if cert_electives_still_needed != 0:
                        is_course_generation_complete = False

                    print(f"Is course generation complete?: {is_course_generation_complete}")

                # if the scheduling is still not complete, update semester information
                if not is_course_generation_complete:
                    current_semester_credits = 0
                    current_semester_classes = []
                    semester += 1
                    current_semester_cs_math_credits_per_semester = 0
                    current_CS_elective_credits_per_semester = 0
                    print("Advancing to next semester...")
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
        "min_3000_course": min_3000_course_still_needed,
        "include_summer": include_summer,
        "certificate_choice": certificate_choice,
        "num_3000_replaced_by_cert_core": num_3000_replaced_by_cert_core,
        "cert_electives_still_needed": cert_electives_still_needed,
        "saved_minimum_credits_selection": min_credits_per_semester,
        "elective_courses": json.dumps(elective_courses),
    }
