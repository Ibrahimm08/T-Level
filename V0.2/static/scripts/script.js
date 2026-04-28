function ValidatePassword() {
  // Validate password using regex and .test() method
  // Password longer the 8 char, has numbers, uppercase and lowercase, one symbol
  let passwordEntry = document.forms["register-form"]["password"].value;
  let passwordConfirm =
    document.forms["register-form"]["confirm-password"].value;
  // Looks through the string to see if it includes
  // Letters from a-z
  // Letters from A-Z
  // Any digits
  // Any @$!%?& symbols
  // 8 or more characters
  // only limit to A-Z a-z digits @$!%?&
  let pattern =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%?&])[A-Za-z\d@$!%?&]{8,}$/g;

  // check if the password is collected correctly and the result of the test

  console.log(passwordEntry, pattern.test(passwordEntry));
  console.log(!pattern.test(passwordEntry)); // do not remove this line otherwise if statement functions incorrectly

  // Check if password meets security requirements and password confimation matches
  if (!pattern.test(passwordEntry)) {
    alert(
      "Password must contain atleast one symbol(@$!%?&), number, lower and uppercase character!",
    );
    return false;
  } else if (!(passwordEntry === passwordConfirm)) {
    alert("Passwords do not match");
    return false;
  }
}

var fontToggled = false;

function ToggleFont() {
  let h1 = document.querySelectorAll("h1");
  let h2 = document.querySelectorAll("h2");
  let h3 = document.querySelectorAll("h3");
  let h4 = document.querySelectorAll("h4");
  let h5 = document.querySelectorAll("h5");
  let p = document.querySelectorAll("p");

  if (fontToggled == false) {
    h1.forEach((element) => {
      element.setAttribute("style", "font-family: monospace !important;");
    });
    h2.forEach((element) => {
      element.setAttribute("style", "font-family: monospace !important;");
    });
    h3.forEach((element) => {
      element.setAttribute("style", "font-family: monospace !important;");
    });
    h4.forEach((element) => {
      element.setAttribute("style", "font-family: monospace !important;");
    });
    h5.forEach((element) => {
      element.setAttribute("style", "font-family: monospace !important;");
    });
    p.forEach((element) => {
      element.setAttribute("style", "font-family: monospace !important;");
    });
    
    fontToggled = true
  }else{
        h1.forEach((element) => {
      element.setAttribute("style", "font-family: unset;");
    });
    h2.forEach((element) => {
      element.setAttribute("style", "font-family: unset;");
    });
    h3.forEach((element) => {
      element.setAttribute("style", "font-family: unset;");
    });
    h4.forEach((element) => {
      element.setAttribute("style", "font-family: unset;");
    });
    h5.forEach((element) => {
      element.setAttribute("style", "font-family: unset;");
    });
    p.forEach((element) => {
      element.setAttribute("style", "font-family: unset;");
    });
    fontToggled = false
  }
}
