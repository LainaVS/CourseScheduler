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
    const summer_credits_label = document.getElementById("summer_credits_label");
    const summer_credits_select = document.getElementById("summer_credits_select");

    if (!checkbox.checked) {
        starting_semester_dropdown.remove(2); // remove summer option
        summer_credits_label.style.visibility = "hidden";
        summer_credits_select.style.visibility = "hidden";
    } else {
        var option = document.createElement("option");
        option.text = "Summer";
        starting_semester_dropdown.add(option);
        summer_credits_label.style.visibility = "visible";
        summer_credits_select.style.visibility = "visible";
    }
    const certificate_select = document.getElementById('certificate');
    const index_of_cert_value = certificate_select.value.indexOf(',') + 1; // Index will be after comma
    const cert_value = certificate_select.value.substring(index_of_cert_value);

    mobile_cert_check(cert_value);
}

// add or remove credit options depending on Earned Credit checkbox
function handleEarnedCreditCheckboxClick(checkbox) {
    console.log("Function called");
    const waived_credits_label = document.getElementById("waived_courses_label");
    const waived_credits_select = document.getElementById("waived_courses_id");
    const taken_credits_label = document.getElementById("taken_courses_label");
    const taken_credits_select = document.getElementById("taken_courses");
    const credits_earned_label = document.getElementById("total_credits_label");
    const credits_earned_select = document.getElementById("starting_credits");
    const gen_credits_label = document.getElementById("gen_credits_label");
    const free_credits_label = document.getElementById("free_credits_label");

    const second_form = document.getElementById('form-container-2');
    const main = document.getElementById('main-form');
    const pop_up = document.getElementById('test-id');

    if (!checkbox.checked) {
        setVisibilityWithTransition([waived_credits_label, waived_credits_select, taken_credits_label, taken_credits_select, credits_earned_label, credits_earned_select, gen_credits_label, free_credits_label], "hidden");
        setVisibilityWithTransition([gen_credits_id, free_credits_id], "hidden");

        /*remove CSS styling*/
        second_form.classList.remove('form-container-2');
        second_form.classList.remove('main-form');
        second_form.classList.add('shrink');
    } else {
        setVisibilityWithTransition([waived_credits_label, waived_credits_select, taken_credits_label, taken_credits_select, credits_earned_label, credits_earned_select, gen_credits_label, free_credits_label], "visible");
        setVisibilityWithTransition([gen_credits_id, free_credits_id], "visible");

        /*add CSS styling*/
        second_form.classList.add('form-container-2');
        second_form.classList.add('main-form');
        second_form.classList.remove('shrink');
    }
}

function setVisibilityWithTransition(elements, visibility) {
    elements.forEach(element => {
        if (visibility === "visible") {
            element.style.opacity = 1;
        } else {
            element.style.opacity = 0;
        }
        setTimeout(() => {
            element.style.visibility = visibility;
        }, 1000); // Adjust the duration of the transition here (in milliseconds)
    });
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
