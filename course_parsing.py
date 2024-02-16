import xml.etree.ElementTree as ET

# Parse the XML file
tree = ET.parse('xml/course_data.xml')
root = tree.getroot()

# Iterate over each <course> tag
for course in root.findall('.//course'):
    subject = course.find('subject').text
    course_number = course.find('course_number').text
    course_name = course.find('course_name').text
    credit = course.find('credit').text
    rotation_terms = [(rt.find('term').text, rt.find('time_code').text) for rt in course.findall('rotation_term')]
    course_description = course.find('course_description').text

    # Print or process the extracted information as needed
    print(f"Course: {subject} {course_number}: {course_name}")
    print(f"\tCredit: {credit}")
    print(f"\tRotation Terms: {rotation_terms}")
    print(f"\tCourse Description: {course_description[:40]}...")