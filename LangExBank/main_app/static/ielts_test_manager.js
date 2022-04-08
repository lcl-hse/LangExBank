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

var dropdown = function(dropdown_btn) {
  list_id = dropdown_btn.id.split('_');
  list_id = list_id.slice(1, list_id.length);
  list_id = list_id.join("_");
  hidden_list = document.getElementById(list_id);
  if (hidden_list.style.display == "block") {
      hidden_list.style.display = "none";
  } else {
      hidden_list.style.display = "block";
  };
};

// var addTestToCollection = function(test_id, collection_id) {

// };

// var deleteTestFromCollection = function(test_id, collection_id, test_type) {

// };

var deleteCollection = function(collection_id) {
  var token = document.getElementById('token').innerText;
  var collection_div = document.getElementById(`div_collection_${collection_id}`);
  if (confirm(`Are you sure to delete collection ${collection_id}`)) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
      if (this.status == 200) {
          delete_elem(collection_div);
          alert(`Collection ${collection_id} deleted`);
      } else if (this.status >= 400) {
          alert(`Unable to delete collection ${collection_id}`);
      }
    };
    xhttp.open("POST", "/deleteCollection/", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send(`collection_id=${collection_id}&csrfmiddlewaretoken=${token}`);
  } else {
    return;
  };
};