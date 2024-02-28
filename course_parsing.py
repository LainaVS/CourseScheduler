import xmltodict
import json
from collections.abc import Mapping
import xml.etree.ElementTree as ET

# Parse the XML file
tree = ET.parse('xml/course_data.xml')
root = tree.getroot()

# Iterate over each <course> tag
# for course in root.findall('.//course'):
#     subject = course.find('subject').text
#     course_number = course.find('course_number').text
#     course_name = course.find('course_name').text
#     credit = course.find('credit').text
#     rotation_terms = [(rt.find('term').text, rt.find('time_code').text) for rt in course.findall('rotation_term')]
#     course_description = course.find('course_description').text

#     # Print or process the extracted information as needed
#     print(f"Course: {subject} {course_number}: {course_name}")
#     print(f"\tCredit: {credit}")
#     print(f"\tRotation Terms: {rotation_terms}")
#     print(f"\tCourse Description: {course_description[:40]}...")

def build_prerequisites(course):
    prereqs_list = []
    if ('prerequisite' in course.keys()):
        prereqs = course['prerequisite']['or_choice']
        if isinstance(prereqs, Mapping): # Checks if prereqs is a dictionary
            prereqs_list.append(prereqs['and_required'])
        else:
            for prereq in prereqs:
                # Checks if the prequisite is an array or a comp sci/math class prerequisite
                prereq = prereq['and_required']
                if isinstance(prereq, list):
                    prereqs_list.append(prereq)
                elif (prereq.startswith('CMP SCI') or prereq.startswith('MATH')):
                    prereqs_list.append([prereq])
    return prereqs_list
    
def build_dictionary(courses):
    updated_course_dict = {}
    if isinstance(courses, Mapping): # Checks if courses variable is a dictionary
        courses['prerequisite'] = build_prerequisites(courses)
        course_dict = { 
            courses["course_number"]: courses
        }
        updated_course_dict.update(course_dict)
    else:
        for course in courses:
            course['prerequisite'] = build_prerequisites(course)
            course_dict = { 
                course["course_number"]: course 
            }
            updated_course_dict.update(course_dict)   
    return updated_course_dict

def parse_courses():
    with open('xml/course_data.xml') as fd:
        doc = xmltodict.parse(fd.read())
    csbs_req = doc["CSBSReq"]
    core_courses_dict = build_dictionary(csbs_req["CoreCourses"]["course"])
    electives_dict = build_dictionary(csbs_req["Electives"]["course"])
    math_dict = build_dictionary(csbs_req["MathandStatistics"]["course"])
    other_courses_dict = build_dictionary(csbs_req["OtherCourses"]["course"])
    print(json.dumps(core_courses_dict, indent=4))
    print(json.dumps(electives_dict, indent=4))
    print(json.dumps(math_dict, indent=4))
    print(json.dumps(other_courses_dict, indent=4))