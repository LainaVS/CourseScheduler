function drag(ev, course_element) {
    var course_desc = course_element.getAttribute("title");
    var course_num = course_element.getAttribute("courseNum");
    var course_name = course_element.getAttribute("courseName");
    var course_credits = course_element.getAttribute("courseCredits");

    course_element.setAttribute("id", "li_to_move");

    ev.dataTransfer.setData("course_desc", course_desc);
    ev.dataTransfer.setData("course_num", course_num);
    ev.dataTransfer.setData("course_name", course_name);
    ev.dataTransfer.setData("course_credits", course_credits);
    ev.dataTransfer.setData("course_element", course_element);
}

function allowDrop(ev) {
    ev.preventDefault();
}

function dropFailedAlert (msg, li_element) {
    alert(msg);
    li_element.removeAttribute("id");
}

function prereqVerification(course_info, course_num, semester_num, li_to_move, course_name) {
    let alert_message = "";
    let should_move_course = true;
    let required_courses_taken = false;

    const course_schedule = JSON.parse(document.getElementById("course_schedule").value)
    let credits_total_for_new_semester = 0;
    const courses_taken_before_new_semester = [];
    const new_semester_current_courses = [];

    let concurrent = null;

    if (Object.keys(course_info).includes("concurrent")) {
        concurrent = course_info["concurrent"];
    }

    for (let i = 0; i <= semester_num; ++i) {
        course_schedule[i].schedule.forEach((x) => {
            // check if the course is an elective
            const elective = course_name === '[User Selects]';
            
            if (!elective && i != semester_num) {
                courses_taken_before_new_semester.push(x.course);
            }
            if (i == semester_num) {
                new_semester_current_courses.push(x.course);
            }
        });
        credits_total_for_new_semester = credits_total_for_new_semester + course_schedule[i].credits;
    }

    course_info["prerequisite"].some((prereq) => {
        if (Array.isArray(prereq)) {
            if (prereq.length === 1) {
                if (courses_taken_before_new_semester.includes(prereq[0]) ||
                    (new_semester_current_courses.includes(prereq[0]) && (prereq[0] === concurrent))) {
                        required_courses_taken = true;
                        return true;
                } else {
                    alert_message = `${course_num} prerequisite (${prereq[0]}) has to be completed prior to the selected semester!`;
                    required_courses_taken = false;
                }
            } else {
                required_courses_taken = false;

                prereq.forEach((prereq_course) => {
                    if (courses_taken_before_new_semester.includes(prereq_course) ||
                        (new_semester_current_courses.includes(prereq_course) && (prereq_course === concurrent))) {
                            required_courses_taken = true;
                    } else {
                        alert_message = `${course_num} prerequisite (${prereq_course}) has to be completed prior to the selected semester!`;
                        required_courses_taken = false;
                    }
                })
                if (required_courses_taken) {
                    required_courses_taken = true;
                    return true;
                }
            }
        } else {
            if (course_num === "ENGLISH 3130") {
                if (!(credits_total_for_new_semester >= 56)) {
                    alert_message = "ENGLISH 3130 does not meet it's criteria of a minimum of 56 credit hours for the selected semester!";
                    required_courses_taken = false;
                } else if (!courses_taken_before_new_semester.includes(prereq)) {
                    alert_message = `${course_num} prerequisite (${prereq}) has to be completed prior to the selected semester!`;
                    required_courses_taken = false;
                } else {
                    required_courses_taken = true;
                    return true; // Stop looping since class can be added
                }
            } else if ((courses_taken_before_new_semester.includes(prereq) ||
                (new_semester_current_courses.includes(prereq) && (prereq === concurrent)))) {
                    required_courses_taken = true;
            } else {
                alert_message = `${course_num} prerequisite (${prereq}) has to be completed prior to the selected semester!`;
                required_courses_taken = false
            }
        }
    })
    if (!required_courses_taken) {
        dropFailedAlert(alert_message, li_to_move)
        should_move_course = false;
    }
    return should_move_course;
}

function drop(ev, course_element) {
    ev.preventDefault();

    // Can possibly clean up with the use of the li_to_move to get element
    var course_desc = ev.dataTransfer.getData("course_desc");
    var course_num = ev.dataTransfer.getData("course_num");
    var course_name = ev.dataTransfer.getData("course_name");

    var course_credits = parseInt(ev.dataTransfer.getData("course_credits"));

    var li_to_move = document.getElementById("li_to_move");
    let course_schedule = JSON.parse(document.getElementById("course_schedule").value);

    const semester_num = parseInt(course_element.getAttribute("semesterNum"));
    const selected_drop_ul = document.getElementById(`semester-${semester_num}-ul`);

    let should_move_course = true;

    if (course_num === "INTDSC 1003") {
        dropFailedAlert("INTDSC 1003 must be taken in the first semester!", li_to_move);
        should_move_course = false;
    } else if (course_num === "CMP SCI 1000" && semester_num > 1) {
        dropFailedAlert("CMP SCI 1000 must be taken in the first or second semester!", li_to_move);
        should_move_course = false;
    }

    // check if the course is an elective
    const elective = course_name === '[User Selects]';

    if (!elective && should_move_course) {
        var items = selected_drop_ul.getElementsByTagName("li");
        let course_info = null;

        for (var i = 0; i < items.length; ++i) {
            // Check if course is being dropped back into the same semester it was previously in
            if (course_num == items[i].getAttribute("courseNum")) { 
                li_to_move.removeAttribute("id");
                return; // Stop drop() function since the list item is not being dropped in a new semester
            }
        }

        const required_courses_dict_list = JSON.parse(document.getElementById("required_courses_dict_list_unchanged").value);

        required_courses_dict_list.some((course_array) => {
            if (course_array[0] === course_num) {
                course_info = course_array[1];
                return true;
            }
        });

        if (!course_info.semesters_offered.includes(course_schedule[semester_num].semester)) {
            dropFailedAlert(`${course_num} is not offered during the ${course_schedule[semester_num].semester} semester!`, li_to_move)
            should_move_course = false;
        }

        if ((course_info["prerequisite"].length != 0) && should_move_course) {
            should_move_course = prereqVerification(course_info, course_num, semester_num, li_to_move, course_name)
        }
    }

    if (should_move_course) {
        var li_to_move_original_parent = li_to_move.parentNode;
        var li_to_move_original_semester_num = parseInt(li_to_move_original_parent.parentNode.getAttribute("semesterNum"));
        var li_to_move_original_semester_credits_element = document.getElementById(`semester-${li_to_move_original_semester_num}-credits`);
        var li_to_move_original_semester_credits = parseInt(li_to_move_original_semester_credits_element.childNodes[1].textContent);
        var original_semester_updated_credits = li_to_move_original_semester_credits - course_credits;

        var new_li_parent_semester_num = parseInt(selected_drop_ul.parentNode.getAttribute("semesterNum"));
        var new_li_parent_semester_credits_element = document.getElementById(`semester-${new_li_parent_semester_num}-credits`);
        var new_li_parent_semester_credits = parseInt(new_li_parent_semester_credits_element.childNodes[1].textContent);
        var new_semester_updated_credits = new_li_parent_semester_credits + course_credits;

        new_li_parent_semester_credits_element.childNodes[1].textContent = new_semester_updated_credits;

        li_to_move_original_semester_credits_element.childNodes[1].textContent = original_semester_updated_credits;
        
        var added_course = {
            course: course_num,
            credits: course_credits,
            description: course_desc,
            name: course_name
        };

        course_schedule[new_li_parent_semester_num].schedule.push(added_course);
        course_schedule[new_li_parent_semester_num].credits = new_semester_updated_credits;

        var index_of_old_course_location = course_schedule[li_to_move_original_semester_num].schedule.findIndex(i => i.course === course_num);

        if (index_of_old_course_location > -1) { // only splice array when item is found
            course_schedule[li_to_move_original_semester_num].schedule.splice(index_of_old_course_location, 1); // 2nd parameter means remove one item only
            course_schedule[li_to_move_original_semester_num].credits = original_semester_updated_credits;
        }

        document.getElementById("course_schedule").value = JSON.stringify(course_schedule);

        selected_drop_ul.appendChild(li_to_move);
    }
    li_to_move.removeAttribute("id");
}