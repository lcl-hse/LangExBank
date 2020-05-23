delete_elem = function(elem) {
    elem.parentNode.removeChild(elem);
};

deleteQuiz = function(quiz_id, quiz_name) {
  quiz = document.getElementById("quiz_"+quiz_id);
  // console.log("test_"+id);
  // console.log(test)
  token = document.getElementById('token').innerText;
  if (confirm("Are you sure to delete quiz "+ quiz_name +"?")) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.status == 200) {
            delete_elem(quiz);
            alert("Quiz deleted");
        } else if (this.status == 403) {
            alert("Unable to delete quiz "+quiz.name)
        }
    }
    xhttp.open("POST", "/deleteQuiz/", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send("quiz_id="+quiz_id+"&csrfmiddlewaretoken="+token);
  } else {
    return;
  }
};