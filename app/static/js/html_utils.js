// Add or remove 'Summer' option depending on Summer checkbox
function handleSummerCheckboxClick(checkbox){
    var starting_semester_dropdown = document.getElementById("starting_semester");
    if (!checkbox.checked) {
        starting_semester_dropdown.remove(2); // remove summer option
    } else {
        var option = document.createElement("option");
        option.text = "Summer";
        starting_semester_dropdown.add(option);
    }
}

// Remove all options of a passed in select element
function removeOptions(selectElement) {
    var i, L = selectElement.options.length - 1;
    for(i = L; i >= 0; i--) {
        selectElement.remove(i);
    }
}

// Rebuild current credits dropdown based on selected 'Taken' courses 
function handleTakenCourseSelect(sel) {
    var starting_credits_dropdown = document.getElementById("starting_credits");
    var opts = []
    var opt;
    var credits = 0;
    for (var i = 0; i < sel.options.length; i++) {
        opt = sel.options[i];

        if (opt.selected) {
            opts.push(opt.value);
            credits = credits + parseInt(opt.getAttribute("credits"))
        }
    }

    var numArray = [];
    var highEnd = 200; // Max value for current credits option
    c = highEnd - credits + 1;
    while ( c-- ) {
        numArray[c] = highEnd--
    }

    // Remove all option elements from the starting credits dropdown
    removeOptions(starting_credits_dropdown);

    // Updates the starting credits options based on taken courses selected
    for (var i = 0; i < numArray.length; i++) {
        var newOption = document.createElement('option');

        newOption.text = numArray[i];
        newOption.value = numArray[i];

        starting_credits_dropdown.options.add(newOption, null);
    }

    // Update waived courses select element to remove/add options based on selected taken courses
    updateWaivedTakenDropdown(sel, true)
}

// Update waived/taken courses select element to remove/add options based on selected waived/taken courses
function updateWaivedTakenDropdown(sel, is_taken_courses) {
    var dropdown_to_update;
    if (is_taken_courses) {
        dropdown_to_update = document.getElementById("waived_courses");
    } else {
        dropdown_to_update = document.getElementById("taken_courses");   
    }
    var required_courses = JSON.parse(document.getElementById("json_required_courses").value);

    var opts = []
    var selected_opts_from_dropdown_to_update = []
    var opt;

    // Obtain list of selected courses from passed in select
    for (var i = 0; i < sel.options.length; i++) {
        opt = sel.options[i];

        if (opt.selected) {
            opts.push(opt.value);
        }
    }

    // Obtain list of selected courses from select element to be updated (this will allow us to ensure already selected values will remain selected)
    for (var i = 0; i < dropdown_to_update.options.length; i++) {
        opt = dropdown_to_update.options[i];

        if (opt.selected) {
            selected_opts_from_dropdown_to_update.push(opt.value);
        }
    }

    removeOptions(dropdown_to_update);

    // Generates new options for the waived/taken select element
    for (var i = 0; i < required_courses.length; i++) {
        // If the course is not selected in the current element then add that course option element to the other select dropdown
        if (!opts.includes(required_courses[i].course)) {
            var newOption = document.createElement('option');

            newOption.text = required_courses[i].course;
            newOption.value = required_courses[i].course;

            // If Taken courses is not the currently selected element then don't add credits attribute option element
            if (!is_taken_courses) {
                newOption.setAttribute("credits", required_courses[i].credits);
            }

            if (selected_opts_from_dropdown_to_update.includes(required_courses[i].course)) {
                newOption.selected = true
            }

            dropdown_to_update.options.add(newOption, null);
        }
    }
}

function drag(ev, course_element) {
    var course_desc = course_element.getAttribute("title");
    var course_num = course_element.getAttribute("courseNum");
    var course_name = course_element.getAttribute("courseName");
    var course_credits = course_element.getAttribute("courseCredits");

    course_element.setAttribute("id", "li_to_delete");

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

function drop(ev, course_element) {
    ev.preventDefault();

    // Can possibly clean up with the use of the li_to_delete to get element
    var course_desc = ev.dataTransfer.getData("course_desc");
    var course_num = ev.dataTransfer.getData("course_num");
    var course_name = ev.dataTransfer.getData("course_name");
    var course_credits = parseInt(ev.dataTransfer.getData("course_credits"));

    var li_to_delete = document.getElementById("li_to_delete");

    const semester_num = parseInt(course_element.getAttribute("semesterNum"));
    const ul_element = document.getElementById(`semester-${semester_num}-ul`);

    if (course_num === "INTDSC 1003") {
        dropFailedAlert("INTDSC 1003 must be taken in the first semester!", li_to_delete);
        return;
    } else if (course_num === "CMP SCI 1000" && semester_num > 1) {
        dropFailedAlert("CMP SCI 1000 must be taken in the first or second semester!", li_to_delete);
        return;
    }

    let should_move_course = true;

    if (!course_num.toLowerCase().includes("elective")) {
        var items = ul_element.getElementsByTagName("li");

        for (var i = 0; i < items.length; ++i) {
            // Check if course is being dropped back into the same semester it was previously in
            if (course_num == items[i].getAttribute("courseNum")) { 
                li_to_delete.removeAttribute("id");
                return; // Stop drop() function since the list item is not being dropped in a new semester
            }
        }

        let course_info = null;
        let concurrent = null;

        const required_courses_dict_list = JSON.parse(document.getElementById("required_courses_dict_list_unchanged").value);

        required_courses_dict_list.some((course_array) => {
            if (course_array[0] === course_num) {
                course_info = course_array[1];
                return true;
            }
        });

        if (Object.keys(course_info).includes("concurrent")) {
            concurrent = course_info["concurrent"];
        }

        if (course_info["prerequisite"].length != 0) {
            let alert_message = "";
            let required_courses_taken = false;
            const prereqs = course_info["prerequisite"];

            const course_schedule = JSON.parse(document.getElementById("course_schedule").value)
            let credits_total_for_new_semester = 0;
            const courses_taken_before_new_semester = [];
            const new_semester_current_courses = [];

            for (let i = 0; i <= semester_num; ++i) {
                course_schedule[i].schedule.forEach((x) => {
                    if (!x.course.toLowerCase().includes("elective") && i != semester_num) {
                        courses_taken_before_new_semester.push(x.course);
                    }
                    if (i == semester_num) {
                        new_semester_current_courses.push(x.course);
                    }
                });
                credits_total_for_new_semester = credits_total_for_new_semester + course_schedule[i].credits;
            }

            prereqs.some((prereq) => {
                if (Array.isArray(prereq)) {
                    if (prereq.length === 1) {
                        if (courses_taken_before_new_semester.includes(prereq[0]) ||
                            (new_semester_current_courses.includes(prereq[0]) && (prereq[0] === concurrent))) {
                                required_courses_taken = true;
                                return true;
                        } else {
                            alert_message = alert_message !== "" ? alert_message : `${course_num} prerequisite (${prereq[0]}) has to be completed first!`;
                            required_courses_taken = false;
                        }
                    } else {
                        required_courses_taken = false;

                        prereq.forEach((prereq_course) => {
                            if (courses_taken_before_new_semester.includes(prereq_course) ||
                                (new_semester_current_courses.includes(prereq_course) && (prereq_course === concurrent))) {
                                    required_courses_taken = true;
                            } else {
                                alert_message = alert_message !== "" ? alert_message : `${course_num} prerequisite (${prereq_course}) has to be completed first!`;
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
                            alert_message = `${course_num} prerequisite (${prereq}) has yet to be taken!`;
                            required_courses_taken = false;
                        } else {
                            required_courses_taken = true;
                            return true; // Stop looping since class can be added
                        }
                    } else if ((courses_taken_before_new_semester.includes(prereq) ||
                        (new_semester_current_courses.includes(prereq) && (prereq === concurrent)))) {
                            required_courses_taken = true;
                    } else {
                        alert_message = `${course_num} prerequisite (${prereq}) has yet to be taken!`;
                        required_courses_taken = false
                    }
                }
            })
            if (!required_courses_taken) {
                dropFailedAlert(alert_message, li_to_delete)
                should_move_course = false;
            }
        }
    }

    if (should_move_course) {
        var newListItem = document.createElement('li');

        newListItem.title = course_desc;
        newListItem.setAttribute("courseNum", course_num);
        newListItem.setAttribute("courseName", course_name);
        newListItem.setAttribute("courseCredits", course_credits);
        newListItem.draggable=true;
        newListItem.addEventListener('dragstart', function(ev) { drag(ev, this)}, false);

        var course_num_element = document.createElement('p');
        course_num_element.classList.add("course-number");
        course_num_element.textContent = `${course_num}:`;
        course_num_element.appendChild( document.createTextNode( '\u00A0' ) ); // Adds space after the colon

        var course_name_element = document.createElement('p');
        course_name_element.classList.add("course-name");
        course_name_element.textContent = course_name;

        const course_name_num_div = document.createElement('div');
        course_name_num_div.classList.add("course-name-and-num");                

        course_name_num_div.appendChild(course_num_element);
        course_name_num_div.appendChild(course_name_element);
        newListItem.appendChild(course_name_num_div);
        
        ul_element.appendChild(newListItem);

        var new_li_parent = newListItem.parentNode;
        var new_li_parent_semester_num = parseInt(new_li_parent.parentNode.getAttribute("semesterNum"));
        var new_li_parent_semester_credits_element = document.getElementById(`semester-${new_li_parent_semester_num}-credits`);
        var new_li_parent_semester_credits = parseInt(new_li_parent_semester_credits_element.childNodes[1].textContent);
        var new_semester_updated_credits = new_li_parent_semester_credits + course_credits;

        new_li_parent_semester_credits_element.childNodes[1].textContent = new_semester_updated_credits;

        var li_to_delete_parent = li_to_delete.parentNode;
        var li_to_del_semester_num = parseInt(li_to_delete_parent.parentNode.getAttribute("semesterNum"));
        var li_to_del_semester_credits_element = document.getElementById(`semester-${li_to_del_semester_num}-credits`);
        var li_to_del_semester_credits = parseInt(li_to_del_semester_credits_element.childNodes[1].textContent);
        var original_semester_updated_credits = li_to_del_semester_credits - course_credits;

        li_to_del_semester_credits_element.childNodes[1].textContent = original_semester_updated_credits;

        var course_schedule = JSON.parse(document.getElementById("course_schedule").value);
        
        var added_course = {
            course: course_num,
            credits: course_credits,
            description: course_desc,
            name: course_name
        };

        course_schedule[new_li_parent_semester_num].schedule.push(added_course);
        course_schedule[new_li_parent_semester_num].credits = new_semester_updated_credits;

        var index_of_old_course_location = course_schedule[li_to_del_semester_num].schedule.findIndex(i => i.course === course_num);

        if (index_of_old_course_location > -1) { // only splice array when item is found
            course_schedule[li_to_del_semester_num].schedule.splice(index_of_old_course_location, 1); // 2nd parameter means remove one item only
            course_schedule[li_to_del_semester_num].credits = original_semester_updated_credits;
        }

        document.getElementById("course_schedule").value = JSON.stringify(course_schedule);

        li_to_delete.remove();
    }
}
