document.addEventListener("DOMContentLoaded", function () {
    const dropArea = document.getElementById("drop-area");
    const fileInput = document.getElementById("file-selector");
    const uploadForm = document.getElementById("upload-form");
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-status");
    const uploadStatus = document.getElementById("upload-status");

    // Drag-and-drop styling and behavior
    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
        dropArea.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    dropArea.addEventListener("dragover", () => dropArea.classList.add("highlight"));
    dropArea.addEventListener("dragleave", () => dropArea.classList.remove("highlight"));

    dropArea.addEventListener("drop", function (e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            uploadStatus.textContent = `${files.length} screenshot(s) loaded.`;
        } else {
            alert("No screenshots detected in drop.");
        }
    });

    fileInput.addEventListener("change", function () {
        const count = fileInput.files.length;
        uploadStatus.textContent = `${count} screenshot(s) selected.`;
    });

    uploadForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const files = fileInput.files;
        if (files.length === 0) {
            alert("Please upload at least one screenshot.");
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("screenshots", files[i]);
        }

        // ✅ Show progress bar immediately
        progressContainer.style.display = "block";
        progressBar.value = 0;
        progressText.textContent = "Processing, please wait...";

        // Simulate progress (like alliance page)
        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 98) {
                progress += 1;
                progressBar.value = progress;
            }
        }, 1500);

        fetch("/player-info", {
            method: "POST",
            body: formData
        })
        .then(response => {
            if (!response.ok) throw new Error("HTTP " + response.status);
            return response.json();
        })
        .then(data => {
            clearInterval(interval);
            progressBar.value = 100;
            progressText.textContent = "Processing 100%";

            if (data.error) {
                alert("❌ " + data.error);
                return;
            }

            const table = document.getElementById("preview-table");
            table.innerHTML = "";
            const preview = document.getElementById("preview-section");
            preview.style.display = "block";
			console.log("✅ Received response:", data);
            const keys = Object.keys(data.data[0]);
            const headerRow = table.insertRow();
            keys.forEach(key => {
                const th = document.createElement("th");
                th.textContent = key;
                headerRow.appendChild(th);
            });

            data.data.forEach(player => {
                const row = table.insertRow();
                keys.forEach(key => {
                    const cell = row.insertCell();
                    cell.textContent = player[key] || "";
                });
            });

            document.getElementById("download-player-info-excel").onclick = function () {
                window.location.href = data.excel_file;
            };
            document.getElementById("download-buttons").style.display = "block";
        })
        .catch(error => {
            clearInterval(interval);
            console.error("❌ Error:", error);
            alert("Something went wrong. Please try again.");
        });
    });
});
