fetch('https://api.ipify.org?format=json')
    .then(response => response.json())
    .then(data => {
        document.getElementById('ip-address').textContent = data.ip;
    })
    .catch(error => console.error('Error fetching IP address:', error));


window.addEventListener("load", () => {
  clock();
  function clock() {
    const today = new Date();

    // get time components
    const hours = today.getHours();
    const minutes = today.getMinutes();
    const seconds = today.getSeconds();

    //add '0' to hour, minute & second when they are less 10
    const hour = hours < 10 ? "0" + hours : hours;
    const minute = minutes < 10 ? "0" + minutes : minutes;
    const second = seconds < 10 ? "0" + seconds : seconds;

    // get date components
    const month = today.getMonth();
    const year = today.getFullYear();
    const day = today.getDate();

    //declaring a list of all months in  a year
    const monthList = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December"
    ];

    //get current date and time
    const date = monthList[month] + " " + day + ", " + year;
    const time = hour + ":" + minute + ":" + second;

    //combine current date and time
    const dateTime = date + " - " + time;

    //print current date and time to the DOM
    document.getElementById("date-time").innerHTML = dateTime;
    setTimeout(clock, 1000);
  }
});


// Store the correct hashed secret for comparison
const HASHED_SECRET = "652c7dc687d98c9889304ed2e408c74b611e86a40caa51c4b43f1dd5913c5cd0"; // Hashed "1234"

function checkSecret() {
  const userInput = document.getElementById("secret-input").value;

  // Hash the input using the sha256 function from jsSHA
  const hashedInput = sha256(userInput);

  // Compare the hashed input with the predefined HASHED_SECRET
  if (hashedInput === HASHED_SECRET) {
    sessionStorage.setItem("authenticated", "true");
    document.getElementById("login-screen").style.display = "none";
    document.getElementById("secure-table").style.display = "block";
  } else {
    alert("Incorrect secret code!");
  }
}

async function updateContent(event, filename) {
  const contentArea = document.getElementById("content-area");

  try {
      console.log(`Fetching: ${filename}`); // Debugging log
      const response = await fetch(filename);

      if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const htmlContent = await response.text();
      console.log("File content loaded:", htmlContent); // Debugging log

      contentArea.innerHTML = htmlContent; // Insert raw HTML
      contentArea.style.display = "block"; // Show content area

      // Position the content area next to the clicked cell
      const cell = event.target.closest("td");
      if (cell) {
          const rect = cell.getBoundingClientRect();
          contentArea.style.position = "absolute";
          contentArea.style.top = `${rect.top + window.scrollY}px`;
          contentArea.style.left = `${rect.right + 10}px`;
      }
  } catch (error) {
      console.error("Error loading file:", error);
      contentArea.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
  }
}




// Hide content when clicking elsewhere
document.addEventListener("click", function (event) {
  let contentArea = document.getElementById("content-area");
  if (!event.target.closest("td")) {
    contentArea.style.display = "none";
  }
});

// Check if already authenticated
if (sessionStorage.getItem("authenticated") === "true") {
  document.getElementById("login-screen").style.display = "none";
  document.getElementById("secure-table").style.display = "block";
}

async function hash(input) {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

// Function to trigger hashing on button click
async function hashSecret() {
  const input = document.getElementById("input-secret").value;
  if (input) {
    const hashed = await hash(input);
    document.getElementById("hash-output").innerText = `Hash: ${hashed}`;
  } else {
    alert("Please enter a secret!");
  }
}