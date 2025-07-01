import React from 'react';
import { extractTopics } from '../api/backend';

function TopicPanel({ notes, onTopicsExtracted }) {
    const handleExtract = async () => {
        const result = await extractTopics(notes);
        onTopicsExtracted(result);
    };

    return (
        <div className="block">
            <h2>Topics</h2>
            <button onClick={handleExtract}>Extract Topics</button>
        </div>
    );
}

export default TopicPanel;