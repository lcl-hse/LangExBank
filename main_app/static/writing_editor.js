var changeWritingAttachment = function(selector){
    attachment = document.getElementById("writingAttachment");
    if (selector.value == "text") {
        new_html = '<textarea class="rich_editor" name="rich_editor" id="rich_editor" rows="30"></textarea>';
        attachment.innerHTML = new_html
        addMCE("rich_editor");
    } else if (selector.value == "pdf") {
        new_html = '<b>PDF Upload:</b> <br />\
        <input type="file" \
        name="pdf_upload" id="pdf_input" \
        onchange="pdf_right_preview(this)">\
        </input>\
        <embed id="book" type="application/pdf" style="height: 640px; width: 100%;" controls>\
        </embed>\
        <br />\
        <br />';
        attachment.innerHTML = new_html;
    };
};

var pdf_right_preview = function(e){
    //console.log(e.id);
    upload_id = e.id.split('_').pop();
    //console.log("Upload id: "+upload_id);
    var book = document.getElementById("book");
    book.src = URL.createObjectURL(e.files[0]);
};
