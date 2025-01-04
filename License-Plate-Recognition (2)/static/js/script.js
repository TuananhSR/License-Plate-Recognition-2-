let videoStream;

function startCamera(videoElementId) {
    const video = document.getElementById(videoElementId);
    
    // Stop previous video stream if exists
    if (videoStream) {
        stopCamera();
    }

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.play();
            videoStream = stream;
        })
        .catch(error => {
            console.error('Error accessing the camera:', error);
        });
}

function stopCamera() {
    if (videoStream) {
        const tracks = videoStream.getVideoTracks();
        tracks.forEach(track => track.stop());
        videoStream = null;
    }
}

async function captureImage(mode) {
    const video = document.getElementById(`${mode}_video`);
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    const imageData = canvas.toDataURL('image/jpeg');
    const id = document.getElementById(`${mode}_id`).value;

    try {
        const response = await fetch(`/${mode}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData.split(',')[1], id: id }),
        });

        if (!response.ok) {
            throw new Error('Failed to capture image.');
        }

        const result = await response.json();
        const messageElement = document.getElementById(`${mode}_message`);
        messageElement.textContent = result.message;
        
        // Remove previous class if exists
        messageElement.classList.remove('success', 'error');

        // Add appropriate class based on response status
        if (result.status === 'success') {
            messageElement.classList.add('success');
        } else {
            messageElement.classList.add('error');
        }

        const imageElement = document.getElementById(`${mode}_image`);
        imageElement.src = `data:image/jpeg;base64,${result.image}`;
        imageElement.style.display = 'block';

    } catch (error) {
        console.error('Error capturing image:', error);
    }
}

