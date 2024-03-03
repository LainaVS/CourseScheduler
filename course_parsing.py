import xmltodict
import json
from collections.abc import Mapping
import xml.etree.ElementTree as ET
from typing import Union

# Parse the XML file
tree = ET.parse('xml/course_data.xml')
root = tree.getroot()

def print_dictionary(course_dictionary: dict) -> None:
    """
    prints a dictionary in readable format
    :param  course_dictionary: dict
    """
    print(json.dumps(course_dictionary, indent=4))

def build_prerequisites(course: dict) -> list:
    """
    Creates the list of pre-requisites for a given course.

    :parameter
    ----------
    course:     dict
                holds all information about a particular course, including
                `subject`, `course_number`, etc. (the keys of the dictionary).
    :return:    list
                this will hold either:
                - a single list of courses that are pre-requisites
                - a lists of lists: i.e. multiple lists of possible pre-requisites.
    """
    # creates an empty list to hold any potential pre-requisites
    prereqs_list = []

    # determines if the course has a pre-requisite
    if ('prerequisite' in course.keys()):
        prereqs = course['prerequisite']['or_choice']

        # prerequisite is a dictionary (i.e. one pre-requisite)
        if isinstance(prereqs, Mapping):
            prereqs_list.append(prereqs['and_required'])

        # prerequisite is a list of dictionaries (i.e. multiple pre-requisites)
        else:
            for prereq in prereqs:
                # Checks if the prequisite is an array or a comp sci/math class prerequisite
                prereq = prereq['and_required']
                if isinstance(prereq, list):
                    prereqs_list.append(prereq)
                elif (prereq.startswith('CMP SCI') or prereq.startswith('MATH')):
                    prereqs_list.append([prereq])

    # flatten lists of >1 length to keep consistency
    if len(prereqs_list) == 1 and isinstance(prereqs_list[0], list):
        prereqs_list = prereqs_list[0]
    return prereqs_list
    
def build_dictionary(courses: Union[dict, list]) -> dict:
    """
    Builds a dictionary with the information of each course of a certain type.

    :parameters
    -----------
    courses:    dict or list
                holds the information for all courses of a certain type (core,
                electives, etc.).

                This parameter is a list of dictionaries if
                there are multiple courses of a certain type. In each dictionary,
                each key is the XML tag, i.e. `subject`, `course_number`, etc.
                with the corresponding value.

                This parameter is a single dictionary if there is only
                one course of that type. In the dictionary, each key is the XML tag, i.e. `subject`,
                `course_number`, etc. with the corresponding value.

    :returns:   dict
                The finalized dictionary of the course type.
                Each key is the course number.
                The corresponding value is a dictionary holding all of the information
                about that course number.

    -----------

    """
    # create empty dict to store course information
    updated_course_dict = {}

    if isinstance(courses, Mapping): # Checks if 'courses' is a dictionary
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
    holds each course type as a key and each value for the key is either
        a list(if only one course for that key exists) or
        a dictionary (if multiple courses for that key exist)

    :parameter
    ----------
    course_type:    str
                    defines the XML tag for the first child of the root, i.e.
                    CoreCourses, Electives, etc.
    course_tag      str
                    defines the XML tag for the first child of the course_type

    :returns
    ---------
    returns         dict
                    The dictionary that holds all course information
    """
    # open xml document to begin parsing
    with open('xml/course_data.xml') as fd:
        doc = xmltodict.parse(fd.read())

    # create a dictionary with course information to further parse
    csbs_req = doc["CSBSReq"]

    # return finalized dictionary of the course type
    return build_dictionary(csbs_req[course_type][course_tag])

def schedule_courses():
    # create course dictionaries
    core_courses = parse_courses("CoreCourses", "course")
    elective_courses = parse_courses("Electives", "course")
    math_courses =parse_courses("MathandStatistics", "course")
    other_courses = parse_courses("OtherCourses", "course")

    required_courses = core_courses.update(math_courses)

    required_courses_list = sorted(list(required_courses.items()), key=lambda d: d[1]["course_number"])

    classes_taken = []
    current_semester_classes = []

    classes_per_semester = 5 # update later to be user input

    for i in range(0, classes_per_semester):
        for x in core_courses_list:

