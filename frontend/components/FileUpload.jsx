import React, { useState } from 'react';
import { uploadPDF } from '../api/backend';

function FileUpload({ onNotesGenerated }) {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleUpload = async () => {
        setLoading(true);
        try {
            let fullNotes = '';
            await uploadPDF(file, (chunk) => {
                fullNotes += chunk;
                onNotesGenerated(fullNotes);
            });
        } catch (error) {
            console.error("❌ Upload failed:", error);  // ← LOG THIS
            alert(error.message);
        }
        setLoading(false);
    };

    return (
        <div className="block">
            <h2>Upload PDF</h2>
            <input type="file" onChange={(e) => setFile(e.target.files[0])} />
            <button onClick={handleUpload} disabled={!file || loading}>
                {loading ? 'Processing...' : 'Generate Notes'}
            </button>
        </div>
    );
}

export default FileUpload;
