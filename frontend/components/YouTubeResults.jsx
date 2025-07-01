import React, { useEffect, useState } from 'react';
import { fetchYouTubeVideos } from '../api/backend';

function YouTubeResults({ topics }) {
    const [results, setResults] = useState([]);

    useEffect(() => {
        const getVideos = async () => {
            const data = await fetchYouTubeVideos(topics);
            setResults(data);
        };
        getVideos();
    }, [topics]);

    return (
        <div className="block">
            <h2>YouTube Videos</h2>
            {results.map((entry, idx) => (
                <div key={idx} className="video-block">
                    <h3>{entry.topic}</h3>
                    <ul>
                        {entry.videos?.map((vid, i) => (
                            <li key={i}>
                                <a href={vid.url} target="_blank" rel="noopener noreferrer">
                                    {vid.title}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            ))}
        </div>
    );
}

export default YouTubeResults;