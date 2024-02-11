# CourseScheduler

### XML Parsing
There are two files that we are currently working with:
* `bscs_degree_reqs.xml` (NEEDS UPDATING FROM JANIKOW): this file only handles the basic information of each required class:
  * subject
  * course_number
  * course_name
<br>I would anticipate that this would be our "master" document that we work mostly off of.
<br>Note that we still have 5 student-chosen elective classes NOT on this xml file.
* `course_rotation.xml` (NEEDS UPDATING FROM JANIKOW): this file has more specific information about each course:
  * semesters offered
  * time

We still need to work with one more file to bring everything together:
* `courses_2016.xml` (NEEDS UPDATING FROM JANIKOW): this file will get the very important pre-requisite information. This is the only necessary information not included. 

### Data Structure
I started building a bit of what the data structure that will hold each course might look like. It could hold the following information:
* `subject`
* `course_number`
* `course_name`
* `terms` (probably store as an additional dict with each term and a bool?)
* `time_codes`(probably store as an additional dict with each time_code and a bool?)