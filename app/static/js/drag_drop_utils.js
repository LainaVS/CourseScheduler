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
}

function allowDrop(ev) {
    ev.preventDefault();
}

function dropFailedElementUpdate (should_add_warning, li_to_update, msg, course_num) {
    if (should_add_warning) {
        if (!document.getElementById(`${course_num}-quest-icon`)) {
            li_to_update.style.border = "1px solid red";

            question_mark_icon = document.createElement("i");
            // The class information added is imported at the top of the schedule_display_page.html
            question_mark_icon.classList.add("fa");
            question_mark_icon.classList.add("fa-question-circle");
            question_mark_icon.title = msg;   
            question_mark_icon.style.color = "red";
            question_mark_icon.setAttribute("id", `${course_num}-quest-icon`);

            children = li_to_update.childNodes;
            for (i = 0; i < children.length; ++i) {
                if (children[i].nodeName === "DIV") {
                    children[i].prepend(question_mark_icon);
                    break;
                }
            }
        }
    } else {
        icon_element = document.getElementById(`${course_num}-quest-icon`);
        if (icon_element) {
            icon_element.remove();
        }
        li_to_update.style.border = null;
    }
}

function prereqVerification(course_info, course_num, semester_num, li_to_move, course_name, is_prereq_for_check = false, orig_course_num) {
    let li_to_update = li_to_move;

    let required_courses_taken = false;

    let failed_message = "";
    const course_schedule = JSON.parse(document.getElementById("course_schedule").value)
    let credits_total_for_new_semester = 0;
    const courses_taken_before_new_semester = [];
    const new_semester_current_courses = [];

    let concurrent = null;

    if (Object.keys(course_info).includes("concurrent")) {
        concurrent = course_info["concurrent"];
    }

    if (!is_prereq_for_check) {
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
    } else {
        li_to_update = document.getElementById(course_num)
        let semester_of_prereq_course = null;
        course_schedule.some((semester) => {
            semester_schedule = semester.schedule.map(x => x.course);
            if (semester_schedule.includes(course_num)) {
                semester_of_prereq_course = semester.semester_number;
            }

            credits_to_remove = 0;
            if (semester.semester_number === semester_num && !semester_of_prereq_course) {
                courses_taken_before_new_semester.push(orig_course_num);
            } else if (semester.semester_number === semester_of_prereq_course) {
                new_semester_current_courses.push(orig_course_num);
            }
            semester.schedule.forEach((course_information) => {
                if (!(course_information.course === orig_course_num)) {
                    if (!semester_of_prereq_course) {
                        courses_taken_before_new_semester.push(course_information.course);
                    } else {
                        new_semester_current_courses.push(course_information.course);
                    }
                } else {
                    credits_to_remove = course_information.credits;
                }
            });
            credits_total_for_new_semester = credits_total_for_new_semester + semester_schedule.credits - credits_to_remove;
            if (semester_of_prereq_course) {
                return true;
            }
        });
    }

    course_info["prerequisite"].some((prereq) => {
        if (Array.isArray(prereq)) {
            if (prereq.length === 1) {
                if (courses_taken_before_new_semester.includes(prereq[0]) ||
                    (new_semester_current_courses.includes(prereq[0]) && (prereq[0] === concurrent))) {
                        required_courses_taken = true;
                        return true;
                } else {
                    failed_message = `${course_num} prerequisite (${prereq[0]}) has to be completed prior to the selected semester!`;
                    required_courses_taken = false;
                }
            } else {
                required_courses_taken = false;

                prereq.some((prereq_course) => {
                    if (courses_taken_before_new_semester.includes(prereq_course) ||
                        (new_semester_current_courses.includes(prereq_course) && (prereq_course === concurrent))) {
                            required_courses_taken = true;
                    } else {
                        failed_message = `${course_num} prerequisite (${prereq_course}) has to be completed prior to the selected semester!`;
                        required_courses_taken = false;
                    }
                    if (!required_courses_taken) {
                        return true;
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
                    failed_message = "ENGLISH 3130 does not meet it's criteria of a minimum of 56 credit hours for the selected semester!";
                    required_courses_taken = false;
                } else if (!courses_taken_before_new_semester.includes(prereq)) {
                    failed_message = `${course_num} prerequisite (${prereq}) has to be completed prior to the selected semester!`;
                    required_courses_taken = false;
                } else {
                    required_courses_taken = true;
                    return true; // Stop looping since class can be added
                }
            } else if ((courses_taken_before_new_semester.includes(prereq) ||
                (new_semester_current_courses.includes(prereq) && (prereq === concurrent)))) {
                    required_courses_taken = true;
            } else {
                failed_message = `${course_num} prerequisite (${prereq}) has to be completed prior to the selected semester!`;
                required_courses_taken = false
            }
        }
    })

    let msg = "";
    if (is_prereq_for_check && !required_courses_taken) {
        msg = `${course_num} failed prerequisite validation after ${orig_course_num} was moved. `.concat(failed_message);
    } else if (!required_courses_taken) {
        msg = `${course_num} failed prerequisite validation after moving. `.concat(failed_message);
    }

    dropFailedElementUpdate(!required_courses_taken, li_to_update, msg, course_num);
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

    const failed_prereq_for_courses = [];

    if (course_num === "INTDSC 1003") {
        if (semester_num === 0) {
            dropFailedElementUpdate(false, li_to_move, null, course_num);
        } else {
            dropFailedElementUpdate(true, li_to_move, "INTDSC 1003 must be taken in the first semester!", course_num);
        }
    } else if (course_num === "CMP SCI 1000") {
        if (semester_num <= 1) {
            dropFailedElementUpdate(false, li_to_move, null, course_num);
        } else {
            dropFailedElementUpdate(true, li_to_move, "CMP SCI 1000 must be taken in the first or second semester!", course_num);
        }
    } else {
        // check if the course is an elective
        const elective = course_name === '[User Selects]';

        if (!elective) {
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

            let should_validate_prereqs = true;

            if (!course_info.semesters_offered.includes(course_schedule[semester_num].semester)) {
                let msg = `${course_num} is not offered during the ${course_schedule[semester_num].semester} semester!`;
                dropFailedElementUpdate(true, li_to_move, msg, course_num);
                should_validate_prereqs = false;
            } else {
                dropFailedElementUpdate(false, li_to_move, null, course_num);
            }

            if ((course_info["prerequisite"].length != 0) && should_validate_prereqs) {
                prereqVerification(course_info, course_num, semester_num, li_to_move, course_name)
            }

            course_prereqs_for = JSON.parse(document.getElementById("course_prereqs_for").value);
            course_prereqs_for_selected_course = course_prereqs_for[course_num]

            if (course_prereqs_for_selected_course) {
                course_prereqs_for_selected_course.forEach((prereq) => {
                    prereq_for_course_info = null;
                    required_courses_dict_list.some((course_array) => {
                        if (course_array[0] === prereq) {
                            prereq_for_course_info = course_array[1];
                            return true;
                        }
                    });
                    required_courses_taken = prereqVerification(prereq_for_course_info, prereq, semester_num, li_to_move, null, true, course_num);
                    if (!required_courses_taken) {
                        failed_prereq_for_courses.push(prereq)
                    }
                })
            }
        }        
    }


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

    li_to_move.setAttribute("id", course_num);
    selected_drop_ul.appendChild(li_to_move);
}