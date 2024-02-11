import xml.etree.ElementTree as ET

# the xml file only goes to 2020, so we can set this later.
YEAR_OF_NEWEST_DATA = "2020"

# set up files
degree_reqs_tree = ET.parse('xml/bscs_degree_reqs.xml')
degree_reqs_root = degree_reqs_tree.getroot()
rotation_tree = ET.parse('xml/course_rotation.xml')
rotation_root = rotation_tree.getroot()
courses_tree = ET.parse('xml/courses_2016.xml')
courses_root = courses_tree.getroot()

def process_course_data(course):
    """
    This function parses an xml file, looking for a specific tag, and printing data from it

    :param      course: the xml tag (only 2 tags are currently possible)
    :return:    void (as of right now)
    """

    # the course data structure might look like this
    subject = ""
    course_number = ""
    course_name = ""
    terms = [] #obviously a better data structure is needed here.
    time_codes = [] #obviously a better data structure is needed here.

    # immediately extract information from the parameter tag
    subject = course.findtext('subject')
    course_number = course.findtext('course_number')
    course_name = course.findtext('course_name')

    # find current course in the current year, in the rotation file
    for rotation_year in rotation_root.findall(f'.//rotation_year[year = "{YEAR_OF_NEWEST_DATA}"]'):

        # look for course in that year
        for current_course in rotation_year.findall('course'):
            current_course_number = current_course.findtext('course_number')

            # look for course number in that course
            if current_course_number == course_number:

                # iterate through every rotation term to ensure all are stored
                for rotation_term in current_course.findall('rotation_term'):
                    terms.append(rotation_term.findtext('term'))
                    time_codes.append(rotation_term.findtext('time_code'))
    print(f"{subject} {course_number} {course_name} {terms} {time_codes}")

# iterate over the reqs file, finding all 'corecourse' tags, store information about each course
for corecourse in degree_reqs_root.findall('.//corecourse'):
    process_course_data(corecourse)

# iterate over the reqs file, finding all 'course' tags, store information about each course
for course in degree_reqs_root.findall('.//course'):
    process_course_data(course)