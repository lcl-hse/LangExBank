// var deleteElem = function(elem_id) {
//     var elem = document.getElementById(elem_id);
//     elem.parentNode.removeChild(elem);
// };

// var deleteQuestion = function(question_id) {
//     alert("Delete Question "+question_id+"?");
// };

// var deleteAnswer = function(answer_id, question_id) {
//     alert("Delete Answer "+answer_id+" to Question "+question_id+"?");
// };

var currAddedAnswerId = -1;
var currAddedWAnswerId = -1;

var delete_elem = function(elem) {
    elem.parentNode.removeChild(elem);
};

var deleteNewWAnswer = function(deleteButton) {
    answerDiv = deleteButton.parentNode;
    delete_elem(answerDiv);
    currAddedWAnswerId += 1;
}

//taken from https://stackoverflow.com/questions/4793604/how-to-insert-an-element-after-another-element-in-javascript-without-using-a-lib :
var insertAfter = function(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
}

var insertBefore = function(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode)
}

var addAnswer = function(last, question_id) {
    newDiv = document.createElement("div");
    newAnswer = document.createElement("input");
    newAnswer.type = "text";
    newAnswer.className = "myInputText";
    newAnswer.name = "answer_"+question_id+"_"+currAddedAnswerId;
    newAnswer.id = question_id+"_"+currAddedAnswerId;
    newAnswer.cols = 80;
    newAnswer.rows = 3;
    currAddedAnswerId -= 1;
    newDiv.appendChild(newAnswer);
    newDiv.innerHTML += '<button onclick="deleteNewAnswer(this)">X</button>';
    insertBefore(newDiv, last)
};

var addWrongAnswer = function(last, question_id) {
    newDiv = document.createElement("div");
    newAnswer = document.createElement("input");
    newAnswer.type = "text";
    newAnswer.className = "myInputText";
    newAnswer.name = "wanswer_"+question_id+"_"+currAddedAnswerId;
    newAnswer.id = question_id+"_"+currAddedAnswerId;
    newAnswer.cols = 80;
    newAnswer.rows = 3;
    currAddedWAnswerId -= 1;
    newDiv.appendChild(newAnswer);
    newDiv.innerHTML += '<button onclick="deleteNewWAnswer(this)">X</button>';
    insertBefore(newDiv, last)
};

var submitEditingForm = function() {
    $('textarea').each(function () {
        var id_nic = $(this).attr('id');
        var nic = new nicEditors.findEditor(id_nic);
        var newContent = nic.getContent()
        document.getElementById(id_nic).value = newContent;
    });
    document.getElementById("editForm").submit();
};

var restoreQuestion = function(question_id) {
    // console.log(question_id);
    question = document.getElementById(question_id);
    var nic = tinymce.get("question_"+question_id);
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.status == 200) {
            nic.setContent(this.responseText);
        };
    };
    xhttp.open("GET", "?question_id="+question_id, true);
    xhttp.send();
};

var restoreAnswer = function(restoreButton) {
    answer_id = restoreButton.id.slice(8);
    answer = document.getElementById(answer_id);
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.status == 200) {
            answer.value = this.responseText;
        };
    };
    answer_id = answer_id.split("_")[1];
    xhttp.open("GET", "?answer_id="+answer_id, true);
    xhttp.send();
};

var restoreWrongAnswer = function(restoreButton) {
    wanswer_id = restoreButton.id.slice(8);
    wanswer = document.getElementById(wanswer_id);
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.status == 200) {
            wanswer.value = this.responseText;
        };
    };
    wanswer_id = wanswer_id.split("_")[2];
    xhttp.open("GET", "?wanswer_id="+wanswer_id, true);
    xhttp.send();
};

var changeNumQuest = function() {
    numSelector = document.getElementById("QuestionCount");
    window.location.replace(window.location.href.split('?')[0]+"?max_q="+numSelector.value)
};

var toBottom = function() {
    window.scrollTo(0,document.body.scrollHeight);
};

var toTop = function() {
    window.scrollTo(0,0);
};

var addMCEWithContent = function(elem_id, html_text, height=456) {
    // elem = document.getElementById(elem_id);
    tinymce.init({
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
    });
};