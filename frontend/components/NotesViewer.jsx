import React, { useEffect, useState } from 'react';

function NotesViewer() {
    const [notes, setNotes] = useState([]);

    useEffect(() => {
        fetch('http://localhost:8000/notes/get_all')
            .then(res => res.json())
            .then(data => setNotes(data));
    }, []);

    return (
        <div className="notes-viewer">
            {notes.map((note, index) => (
                <div key={index} className="note">
                    <h3>{note.title}</h3>
                    <p>{note.content}</p>
                </div>
            ))}
        </div>
    );
}

export default NotesViewer;