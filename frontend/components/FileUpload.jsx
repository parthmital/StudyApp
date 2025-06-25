import React from 'react';

function FileUpload() {
    const handleUpload = (e) => {
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);

        fetch('http://localhost:8000/ocr/upload_pdf', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then(data => console.log(data));
    };

    return (
        <div className="upload-container">
            <input type="file" onChange={handleUpload} />
        </div>
    );
}

export default FileUpload;