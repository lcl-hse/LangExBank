var delete_elem = function(elem) {
    elem.parentNode.removeChild(elem);
};

var deleteTest = function(test_id, test_name) {
  var test = document.getElementById(`test_${test_id}`);
  // console.log("test_"+id);
  // console.log(test)
  var token = document.getElementById('token').innerText;
  if (confirm(`Are you sure to delete test ${test_name}?`)) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.status == 200) {
            delete_elem(test);
            alert(`Test ${test_name} deleted`);
        } else if (this.status >= 400) {
            alert(`Unable to delete test ${test_name}`)
        }
    }
    xhttp.open("POST", "/deleteIELTSTest/", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send(`test_id=${test_id}&csrfmiddlewaretoken=${token}`);
  } else {
    return;
  }
};

var deleteActivity = function(assignment_div, test_name, activity_type) {
  var token = document.getElementById('token').innerText;
  if (confirm(`Are you sure to delete test ${test_name}?`)) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.status == 200) {
            delete_elem(assignment_div);
            alert(`Test ${test_name} deleted`);
        } else if (this.status >= 400) {
            alert(`Unable to delete test ${test_name}`)
        }
    }
    xhttp.open("POST", "/deleteActivity/", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send(`test_name=${test_name}&type=${activity_type}&csrfmiddlewaretoken=${token}`);
  } else {
    return;
  }
};