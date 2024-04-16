function mobile_cert_check(cert_value) {
    const single_semester_submit = document.getElementById('single_semester_submit');
    const complete_schedule_submit = document.getElementById('complete_schedule_submit');
    if (cert_value === 'MOBILECERTReq') {
        if (!document.getElementById("summer").checked) {
            single_semester_submit.disabled = true;
            complete_schedule_submit.disabled = true;
            alert("The Mobile Apps and Computing Certificate requires a course only offered in Summer, so Summer must be selected.")
        } else if (single_semester_submit.disabled && complete_schedule_submit.disabled) {
            single_semester_submit.disabled = false;
            complete_schedule_submit.disabled = false;
        }
    } else if (single_semester_submit.disabled && complete_schedule_submit.disabled) {
        single_semester_submit.disabled = false;
        complete_schedule_submit.disabled = false;
    }
}

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
    const certificate_select = document.getElementById('certificate');
    const index_of_cert_value = certificate_select.value.indexOf(',') + 1; // Index will be after comma
    const cert_value = certificate_select.value.substring(index_of_cert_value);

    mobile_cert_check(cert_value);
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

function handleCertSelect(selectedElement) {
    index_of_cert_value = selectedElement.value.indexOf(',') + 1; // Index will be after comma
    cert_value = selectedElement.value.substring(index_of_cert_value)

    mobile_cert_check(cert_value);
}
