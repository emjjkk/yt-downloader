function startDownload(videoId, downloadType, button) {
    button.disabled = true;
    button.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Starting download...';

    const xhr = new XMLHttpRequest();
    xhr.open('GET', `/download/${videoId}/${downloadType}`, true);

    xhr.onprogress = function(event) {
        if (event.lengthComputable) {
            const percentComplete = (event.loaded / event.total) * 100;
            button.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Downloading... ${percentComplete.toFixed(2)}%`;
        }
    };

    xhr.onload = function() {
        if (xhr.status === 200) {
            button.innerText = 'Download complete!';
            
            // Trigger the download
            const blob = new Blob([xhr.response], { type: 'application/octet-stream' });
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = `${videoId}.${downloadType === 'video' ? 'mp4' : 'm4a'}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Redirect to cleanup after a short delay
            setTimeout(() => {
                window.location.href = '/cleanup';
            }, 2000);
        } else {
            button.innerText = 'Download failed';
            button.disabled = false;
        }
    };

    xhr.onerror = function() {
        button.innerText = 'Download failed';
        button.disabled = false;
    };

    xhr.responseType = 'blob';
    xhr.send();
}

document.getElementById("toggle-details").addEventListener("click", function () {
    const details = document.getElementById("details");
    if (details.classList.contains("hidden")) {
        details.classList.remove("hidden");
        this.textContent = "Hide Details";
    } else {
        details.classList.add("hidden");
        this.textContent = "Show Details";
    }
});
