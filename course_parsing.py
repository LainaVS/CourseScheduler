import xmltodict
import json
from collections.abc import Mapping
import xml.etree.ElementTree as ET
from typing import Union
import copy

# Parse the XML file
tree = ET.parse('xml/course_data.xml')
root = tree.getroot()

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

def parse_courses(course_type: str, course_tag: str) -> dict:
    """
    Parses relevant information from XML and return dictionaries.

    This function opens up the XML file, calls the build_dictionary function
    and returns the dictionary based upon the two parameters provided to
    the function.

    csbs_req is a dictionary that represents a section of parsed XML data. It
    holds each course type as a key and each value for the key is either:
        - a list(if only one course for that key exists) or
        - a dictionary (if multiple courses for that key exist)

    Parameters
    ----------
    course_type:    str
                    defines the XML tag for the first child of the root, i.e.
                    CoreCourses, Electives, etc.
    course_tag      str
                    defines the XML tag for the first child of the course_type

    Returns
    ----------
    dict
                    The dictionary that holds all course information
    """
    # open xml document to begin parsing
    with open('xml/course_data.xml') as fd:
        doc = xmltodict.parse(fd.read())

    # create a dictionary with course information to further parse
    csbs_req = doc["CSBSReq"]

    # return finalized dictionary of the course type
    return build_dictionary(csbs_req[course_type][course_tag])

def add_course(current_semester, course_info, current_semester_classes, course, courses_taken, total_credits_accumulated, current_semester_credits):
    # Add course, credits to current semester and list of courses taken, credits earned
    course_added = False
    if current_semester in course_info['semesters_offered']:
        current_semester_classes.append(course)
        courses_taken.append(course)
        total_credits_accumulated = total_credits_accumulated + int(course_info['credit'])
        current_semester_credits = current_semester_credits + int(course_info['credit'])
        course_added = True
    return course_added, current_semester_classes, courses_taken, total_credits_accumulated, current_semester_credits

def build_semester_list(first_season="Fall", include_fall=True, include_spring=True, include_summer=True) -> list:
    possible_semesters = ["Fall", "Spring", "Summer"]

    # Reorder the seasons based on the user's preference for the first season
    first_index = possible_semesters.index(first_season)
    possible_seasons = possible_semesters[first_index:] + possible_semesters[:first_index]

    # Filter out seasons based on user preferences
    selected_semesters = []
    if include_fall:
        selected_semesters.append("Fall")
    if include_spring:
        selected_semesters.append("Spring")
    if include_summer:
        selected_semesters.append("Summer")

    if first_season not in selected_semesters:
        return ValueError("First season is not in selected seasons")
    if "Fall" not in selected_semesters or "Spring" not in selected_semesters:
        return ValueError("Fall or Spring must be selected")
    return [season for season in possible_seasons if season in selected_semesters]

def schedule_core_courses() -> None:
    """
    Create the multi-semester course schedule for core courses.
    """
    # create dictionaries for each course type
    core_courses = parse_courses("CoreCourses", "course")
    math_courses = parse_courses("MathandStatistics", "course")
    other_courses = parse_courses("OtherCourses", "course")

    # add math and other courses to core courses so that all BSCS requirements are included
    core_courses.update(math_courses)
    core_courses.update(other_courses)

    # sort required courses by course number
    required_courses_list = sorted(list(core_courses.items()), key=lambda d: d[1]["course_number"])
    updated_required_courses_list = copy.deepcopy(required_courses_list)

    # List of just course subject/numbers...do we need?
    # required_courses = sorted(list(core_courses.keys()), key=lambda d: d[0])

    # set user's scheduling preferences
    current_semester = "Spring"
    include_fall = True
    include_spring = True
    include_summer = False
    user_semesters = build_semester_list(current_semester, include_fall, include_spring, include_summer)
    min_credits_per_semester = 15

    # set scheduling information
    semester = 1                                # incremented with each completed semester
    all_courses_selected = False                # ensures that all requirements have been met

    # store temporary semester schedule information
    course_schedule = []
    courses_taken = []
    current_semester_classes = []
    current_semester_credits = 0
    total_credits_accumulated = 0

    min_3000_course = 5

    print(required_courses_list[9])

    # continue adding courses until all requirements have been met
    while (not all_courses_selected):
        course_added = False
        # iterate through list of required courses
        for index, x in enumerate(updated_required_courses_list):
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
                        all_courses_selected = True
                    elif current_semester_credits >= min_credits_per_semester:
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
                        current_semester = user_semesters[(semester + 1) % len(user_semesters)]
                    updated_required_courses_list.pop(index)
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
                all_courses_selected = True
            elif current_semester_credits >= min_credits_per_semester:
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
                current_semester = user_semesters[(semester + 1) % len(user_semesters)]
    print_dictionary(course_schedule)

schedule_core_courses()