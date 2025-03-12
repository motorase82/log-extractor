document.addEventListener("DOMContentLoaded", function () {
    let dropArea = document.getElementById("drop-area");
    let fileInput = document.getElementById("file-input");
    let uploadForm = document.getElementById("upload-form");

    // Prevent default behavior (stop file from opening)
    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
        dropArea.addEventListener(eventName, function (e) {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Highlight drag area when file is dragged over
    dropArea.addEventListener("dragover", function () {
        dropArea.classList.add("highlight");
    });

    dropArea.addEventListener("dragleave", function () {
        dropArea.classList.remove("highlight");
    });

    // Handle dropped files
    dropArea.addEventListener("drop", function (e) {
        let files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            changeMessageAfterFileUpload(); // Change message as soon as the file is dropped
        }
    });

    // Handle file input change event
    fileInput.addEventListener("change", function () {
        console.log("File selected:", fileInput.files[0].name);
        changeMessageAfterFileUpload(); // Change message when file is selected from file input
    });

    // Function to change the message in drop area
    function changeMessageAfterFileUpload() {
        let dropAreaText = document.querySelector('#drop-area p');
        dropAreaText.textContent = "Log File Uploaded! Press Extract Data button to extract the Data";
    }

    // Handle form submission
    uploadForm.addEventListener("submit", function (event) {
        event.preventDefault();
        let formData = new FormData();
        formData.append("file", fileInput.files[0]);

        // Send the data for extraction
        fetch("/upload", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);  // Display custom success message

            // Show the download buttons after data is extracted
            document.getElementById("download-buttons").style.display = "block";
        })
        .catch(error => {
            console.error("Error during fetch:", error); // Handle fetch errors
        });
    });
});
