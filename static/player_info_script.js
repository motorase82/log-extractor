document.addEventListener("DOMContentLoaded", function () {
    const dropArea = document.getElementById("drop-area");
    const fileInput = document.getElementById("file-selector");
    const uploadForm = document.getElementById("upload-form");
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.querySelector("#progress-container p");

    // Highlight drag area
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
			document.querySelector('#drop-area p').textContent = `${files.length} screenshot(s) loaded.`;
		} else {
			alert("No screenshots detected in drop.");
		}

    });

    fileInput.addEventListener("change", function () {
        const count = fileInput.files.length;
        document.querySelector('#drop-area p').textContent = `${count} screenshot(s) selected.`;
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


        progressContainer.style.display = "block";
        progressBar.value = 0;
        progressText.textContent = "Processing, please wait...";

        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 90) {
                progressBar.value = progress;
                progress += 5;
            }
        }, 300);

        fetch("/player-info", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
			clearInterval(interval);
			progressBar.value = 100;
			progressText.textContent = "Done!";

			if (data.error) {
				alert("❌ " + data.error);
				return;
			}

			// Show preview
			const table = document.getElementById("preview-table");
			table.innerHTML = ""; // Clear old data
			const preview = document.getElementById("preview-section");
			preview.style.display = "block";

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

			document.getElementById("download-buttons").style.display = "block";
		})

        })
        .catch(error => {
            clearInterval(interval);
            console.error("❌ Error:", error);
            alert("Something went wrong. Please try again.");
        });
    });
