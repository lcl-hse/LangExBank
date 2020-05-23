delete_elem = function(elem) {
    elem.parentNode.removeChild(elem);
};

deleteTest = function(test_id, test_name) {
  test = document.getElementById("test_"+test_id);
  // console.log("test_"+id);
  // console.log(test)
  token = document.getElementById('token').innerText;
  if (confirm("Are you sure to delete test "+ test_name +"?")) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.status == 200) {
            delete_elem(test);
            alert("Test deleted");
        } else if (this.status == 403) {
            alert("Unable to delete test "+test.name)
        }
    }
    xhttp.open("POST", "/deleteIELTSTest/", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send("test_id="+test_id+"&csrfmiddlewaretoken="+token);
  } else {
    return;
  }
};