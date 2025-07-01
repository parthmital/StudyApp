import React from 'react';

function NotesViewer({ notes }) {
    if (!notes) return null;

    return (
        <div className="block">
            <h2>Generated Notes</h2>
            <pre className="note-box">{notes}</pre>
        </div>
    );
}

export default NotesViewer;