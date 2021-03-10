//taken from https://stackoverflow.com/questions/4793604/how-to-insert-an-element-after-another-element-in-javascript-without-using-a-lib :
var insertAfter = function(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
};

var appendBreak = function(elem) {
    br = document.createElement("br")
    elem.appendChild(br);
};

var testAjaxPost = function(token) {
    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", "/testAjax/", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send("csrfmiddlewaretoken="+token);
};

var delete_elem = function(elem) {
    elem.parentNode.removeChild(elem);
};

var delete_section = function(sectionNode) {
    section_id = sectionNode.id.split("_").pop();
    document.getElementById("secs_to_delete").value += ';'+section_id;
    delete_elem(sectionNode);
};

var delete_question = function(questionNode) {
    question_id = questionNode.id.split("_").pop();
    document.getElementById("questions_to_delete").value += ';'+question_id;
    delete_elem(questionNode);
};

var del_qform = function(section_id, q_id) {
    qform = document.getElementById("qform_"+section_id+"_"+q_id);
    delete_elem(qform);
};

var restore_section = function(section_id) {};

var restore_qform = function(section_id, q_id) {};

var addMCE = function(elem_id, height=undefined, width=undefined) {
    // elem = document.getElementById(elem_id);
    // console.log(width);
    var init_params = {
        selector: 'textarea#'+elem_id,
        paste_data_images: true,
        // image_upload_url: "/imgUpload",
        automatic_uploads: true,
        plugins: [
        "advlist autolink lists link image charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime media table contextmenu paste"
        ],
        toolbar: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image"
    };
    if (height != undefined) {
        init_params.height = height;
    };
    if (width != undefined) {
        init_params.width = width;
    };
    tinymce.init(init_params);
};

var addMCEWithContent = function(elem_id, html_text, height=undefined, width=undefined) {
    // elem = document.getElementById(elem_id);
    var init_params = {
        selector: 'textarea#'+elem_id,
        paste_data_images: true,
        // image_upload_url: "/imgUpload",
        automatic_uploads: true,
        plugins: [
        "advlist autolink lists link image charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime media table contextmenu paste"
        ],
        toolbar: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image",
        setup: function (editor) {
            editor.on('init', function () {
              editor.setContent(html_text);
            });
        }
    };
    if (height != undefined) {
        init_params.height = height;
    };
    if (width != undefined) {
        init_params.width = width;
    };
    tinymce.init(init_params);
};

var allMCEs = function() {
    tinymce.init({
        selector: 'textarea',
        paste_data_images: true,
        // image_upload_url: "/imgUpload",
        automatic_uploads: true,
        plugins: [
        "advlist autolink lists link image charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime media table contextmenu paste"
        ],
        toolbar: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image"
    });
}

var changeAttachment = function(selector, attachment_id) {
    // console.log(attachment_id)
    attachment = document.getElementById(attachment_id);
    att_id = attachment_id.split('_').pop();
    if (selector.value == 'l') {
        new_value = '<b>MP3 Upload:</b> <br />\
        <input type="file" name="audio_upload_'+att_id+'" id="aud_input_'+att_id+'" onchange="aud_preview(this)">\
        </input>\
        <audio id="sound_'+att_id+'" controls>\
        </audio>\
        <br />\
        <br />';
    } else if (selector.value == 'r') {
        new_value = '<b>PDF Upload:</b> <br />\
        <input type="file" \
        name="pdf_upload_'+att_id+'" id="pdf_input_'+att_id+'" \
        onchange="pdf_preview(this)">\
        </input>\
        <embed id="book_'+att_id+'" type="application/pdf" style="height: 400px; width: 100%;" controls>\
        </embed>\
        <br />\
        <br />';
    };
    attachment.innerHTML = new_value;
};

var make_multiple = function(multipleButton) {
    // console.log("entered function make_multiple()");
    sec_quest_id = multipleButton.name.split('_');
    sec_id = sec_quest_id[1];
    quest_id = sec_quest_id[2];
    question_div_id = "qform_"+sec_id+"_"+quest_id;
    question_div = document.getElementById(question_div_id);
    if (multipleButton.checked == true) {
        // console.log("checkbox checked");
        wrong_answer_div = document.createElement("div");
        wrong_answer_div.id = "wrong_answers_"+sec_id+"_"+quest_id
        wrong_answer_div.innerHTML += '<b>Wrong answers</b>: <input type="text" name="wrong_'+sec_id+'_'+quest_id+'"><br /><br />';
        // question_div.appendChild(document.createElement("br"));
        question_div.appendChild(wrong_answer_div);
    } else {
        // туть удаляем это поле;
        // console.log("checkbox not checked");
        wrong_answer_div = document.getElementById("wrong_answers_"+sec_id+"_"+quest_id)
        delete_elem(wrong_answer_div);
    };
};

var addSimpleQuestionForm = function(addButton, section_id) {
    prev_sibl = addButton.previousElementSibling;
    //console.log(prev_sibl)
    curr_id = -1
    if (typeof prev_sibl.id != "undefined") {
        //console.log(prev_sibl.id);
        prev_sibl_id = prev_sibl.id.split('_')[2]
        if (prev_sibl_id < 0) {
            curr_id = prev_sibl_id - 1;
        };
    };
    simple_form = document.createElement("div");
    insertAfter(simple_form, prev_sibl);
    simple_form.id = "qform_"+section_id+"_"+curr_id;
    simple_form.innerHTML += '<b>Text: </b>';
    q_text = document.createElement("textarea");
    simple_form.appendChild(q_text);
    q_text.cols = 10;
    q_text.rows = 1;
    q_text.name = "qtext_"+section_id+"_"+curr_id;
    simple_form.innerHTML += "<b>Answer: </b>";
    a_text = document.createElement("textarea");
    simple_form.appendChild(a_text);
    a_text.cols = 30;
    a_text.rows = 1;
    a_text.name = "atext_"+section_id+"_"+curr_id;
    a_text.id = a_text.name;
    simple_form.innerHTML += '<button type="button" onclick="del_qform('+section_id+','+curr_id+')">Delete</button>';
    simple_form.innerHTML += '<button type="button" onclick="addField(this.parentNode)">Add another field</button>';
    simple_form.innerHTML += '<input type="checkbox" name="insensitive_'+section_id+'_'+curr_id+'"> Case insensitive';
    simple_form.innerHTML += '<input type="checkbox" name="sequence_'+section_id+'_'+curr_id+'"> Multiple letters';
    simple_form.innerHTML += '<input type="checkbox" name="multiple_'+section_id+'_'+curr_id+'" onchange="make_multiple(this)"> Multiple Choice question';
};

var aud_preview = function(e){
    upload_id = e.id.split('_').pop();
    var sound = document.getElementById('sound_'+upload_id);
    sound.src = URL.createObjectURL(e.files[0]);
    // not really needed in this exact case, but since it is really important in other cases,
    // don't forget to revoke the blobURI when you don't need it
    sound.onend = function(elem) {
        URL.revokeObjectURL(elem.src);
    }
};

var img_preview = function(e){
    upload_id = e.id.split('_').pop();
    var img = document.getElementById('img_'+upload_id);
    img.src = URL.createObjectURL(this.files[0]);
};

var pdf_preview = function(e){
    //console.log(e.id);
    upload_id = e.id.split('_').pop();
    //console.log("Upload id: "+upload_id);
    var book = document.getElementById('book_'+upload_id);
    book.src = URL.createObjectURL(e.files[0]);
};

// Id of newly added section
// Always negative and decreased
// Not be mixed with ids of currently existing questions from the database:
var sec_id = -1;

var addSection = function() {
    sections = document.getElementById("sections");
    appendBreak(sections);
    newSection = document.createElement("div");
    new_name = "section_" + sec_id;
    att_id = "attachment_" + sec_id;
    att_id_embed = "'" + att_id + "'";
    // newSection.className = "section";
    sections.appendChild(newSection);
    newSection.innerHTML += '<b>Name:</b> <input type="text" name="sec_name_'+sec_id+'">\
    <b>Type:</b>\
    <select name="section-type_'+sec_id+'" \
    onchange="changeAttachment(this, '+att_id_embed+')">\
        <option value="r"> Reading </option>\
        <option value="l"> Listening</option>\
    </select>\
    <button type="button" onclick="delete_elem(this.parentNode)">Delete section</button>\
    <br />\
    <br />';
    twoCols = document.createElement("div");
    twoCols.className = "equalCols";
    newSection.appendChild(twoCols);
    sectionTextDiv = document.createElement("div");
    twoCols.appendChild(sectionTextDiv);
    embed_name = "'" + new_name + "'"
    tarea = document.createElement('textarea');
    tarea.cols = 50;
    tarea.rows = 30;
    tarea.name = new_name;
    tarea.id = new_name;
    sectionTextDiv.appendChild(tarea);
    attachmentDiv = document.createElement("div");
    attachmentDiv.id = att_id;
    att_id = att_id.split('_').pop();
    new_value = '<b>PDF Upload:</b> <br />\
    <input type="file" \
    name="pdf_upload_'+att_id+'" id="pdf_input_'+att_id+'" \
    onchange="pdf_preview(this)">\
    </input>\
    <embed id="book_'+att_id+'" type="application/pdf" style="height: 100%; width: 100%;" controls>\
    </embed>\
    <br />\
    <br />';
    attachmentDiv.innerHTML = new_value;
    twoCols.appendChild(attachmentDiv);
    newSection.innerHTML += '<button type="button" onclick="addSimpleQuestionForm(this,'+att_id+')">Add questions</button>';
    // decrementing currently added section id at the end:
    sec_id -= 1;
    addMCE(new_name);
};

var addField = function(questionNode) {
    questionNodeId = questionNode.id.split('_');
    questionId = questionNodeId[1] + '_' + questionNodeId[2];

    fields = questionNode.querySelectorAll(`[id^=atext_${questionId}]`);

    lastField = fields[fields.length-1];

    console.log(fields);
    console.log(lastField);

    lastFieldName = lastField.id.split(':');
    lastFieldId = lastFieldName[lastFieldName.length-1];
    lastFieldName = lastFieldName[0];
    if (lastFieldId == lastFieldName) {
        lastFieldId = 0;
    };
    lastFieldId++;

    newSpan = document.createElement("span");

    newField = document.createElement("textarea");
    newField.cols = 30;
    newField.rows = 1;
    newField.name = lastFieldName + ':' + lastFieldId;

    delButton = document.createElement("button");
    delButton.type = 'button';
    delButton.onclick = function() {
        newFieldSpan = this.parentNode;
        questionDiv = newFieldSpan.parentNode;

        questionDiv.removeChild(newFieldSpan);

        // check if it's the last extra field for question:
        if (questionDiv.querySelectorAll(`[id^=atext_${questionId}]`).length == 1) {
            questionDiv.innerHTML += `<span id="singlefieldcheckboxes">\
            <input type="checkbox" name="sequence_${questionId}"> Multiple letters\
            <input type="checkbox" name="multiple_${questionId}"> Multiple Choice question\
            </span>`;
        };
    };
    delButton.innerHTML = 'X';

    // var deleteNewDiv = function() {
    //     delete_elem(newDiv);
    // };


    newSpan.appendChild(newField);
    newSpan.appendChild(delButton);
    newSpan.id = newField.name;

    // Delete DIV for wrong answers (if exists):
    wrong_answer_div = document.getElementById(`wrong_answers_${questionId}`);
    if (wrong_answer_div != undefined) {
        delete_elem(wrong_answer_div);
    };
    // Delete checkboxes for incompatible options
    checkboxes = questionNode.querySelector(`[id="singlefieldcheckboxes"]`);

    if (checkboxes!=undefined) {
        delete_elem(checkboxes);
    };
    insertAfter(newSpan, lastField);
};