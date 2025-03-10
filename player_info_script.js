document.addEventListener("DOMContentLoaded", function () {
    let dropArea = document.getElementById("drop-area");
    let fileInput = document.getElementById("file-input");
    let uploadForm = document.getElementById("upload-form");
    let dataTableBody = document.getElementById("data-table-body");

    // Initialize DataTable only once (on the first load)
    let dataTable = null;

    // Initialize DataTable if it is not already initialized
    function initializeDataTable() {
        if (!$.fn.dataTable.isDataTable('#data-table')) {
            dataTable = $('#data-table').DataTable({
                "ordering": true,
                "paging": true,
                "searching": true,  // Enable searching within all columns
                "lengthChange": true,  // Allow the "Show entries" dropdown
                "pageLength": 90  // Default entries per page
            });
        }
    }

    // Call initialize only once when the page loads
    initializeDataTable();

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

        // Debugging: Log the formData to see what is being sent
        console.log("Sending form data:", formData);

        fetch("/upload", { // Ensure this endpoint is correct
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log("Response received:", data);  // Check what response is returned
            alert(data.message);  // Display custom success message

            // Dynamically add data to the table without reinitializing DataTable
            let tableBody = document.getElementById("data-table-body");

            // Clear previous data in the table
            dataTable.clear();

            // Loop through the extracted data and add rows
            data.data.forEach(row => {
                dataTable.row.add([
                    row.player_name,
                    row.game_id,
                    row.cp,
                    row.sex,
                    row.like_count,
                    row.army_kill
                ]);
            });

            // Draw the table after adding new data
            dataTable.draw();

            // Show the download buttons after data is extracted
            document.getElementById("download-buttons").style.display = "block";
        })
        .catch(error => {
            console.error("Error during fetch:", error); // Handle fetch errors
        });
    });
});
