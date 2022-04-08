var addMCE = function(elem_id, height=456) {
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
        toolbar: "paste | forecolor backcolor | insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image",
        paste_retain_style_properties: "all"
    });
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
        toolbar: "paste | forecolor backcolor | insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image",
        paste_retain_style_properties: "all",
        setup: function (editor) {
            editor.on('init', function () {
              editor.setContent(html_text);
            });
        }
    });
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
        toolbar: "paste | forecolor backcolor | insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image",
        paste_retain_style_properties: "all"
    });
};

var deleteElem = function(elem) {
    elem.parentNode.removeChild(elem);
};

var deleteParent = function(elem) {
    deleteElem(elem.parentNode);
};

var deleteGrandParent = function(elem) {
    deleteParent(elem.parentNode);
};

var addSpan = function() {
    select = document.getElementById("tags");
    selectedTag = select.options[select.selectedIndex];
    shName = selectedTag.value;
    fName = selectedTag.text;
    tagsArea = document.getElementById("selectedTags");

    if (tagsArea.querySelector('#'+shName) == null) {
        tag = document.createElement("span");
        tag.id = shName;

        hidden_inp = document.createElement("input");
        hidden_inp.type = "hidden";
        hidden_inp.name = shName;
        tag.appendChild(hidden_inp);

        tagText = document.createElement("span");
        tagText.className = "tagLabel";
        tagText.innerHTML = ' '+fName+' ';
        delButton = document.createElement("span");
        delButton.setAttribute('onclick', 'deleteGrandParent(this)');
        delButton.innerHTML = "X";
        tagText.appendChild(delButton);
        tag.appendChild(tagText);

        tag.innerHTML += ' ';

        tagsArea.appendChild(tag);
    }
};

var deleteArticle = function(articleNode) {
    var articleName = articleNode.id;
    if (confirm("Are you sure to delete article "+articleName+"?")) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.status == 200) {
                deleteElem(articleNode);
                alert("Article "+articleName+" deleted");
            } else if (this.status == 403) {
                alert("Unable to delete "+articleName);
            }
        }
        xhttp.open("GET", "/deleteArticle/"+articleName, true);
        xhttp.send();
      } else {
        return;
      }
};