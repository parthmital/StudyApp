const BASE = 'http://localhost:8000';

// 📤 Upload a PDF, stream LLM notes back
export async function uploadPDF(file, onChunk) {
    const formData = new FormData();
    formData.append('file', file);

    let response;
    try {
        response = await fetch(`${BASE}/auto/autonotes`, {
            method: 'POST',
            body: formData,
        });
    } catch (err) {
        throw new Error('🚫 Failed to connect to backend. Is FastAPI running?');
    }

    if (!response.ok || !response.body) {
        throw new Error(`❌ Backend returned ${response?.status || 'no body'}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        onChunk(chunk);
    }
}

// 🧠 Extract topics and headings from generated notes
export async function extractTopics(notes) {
    const res = await fetch(`${BASE}/topics/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(notes),
    });

    if (!res.ok) {
        throw new Error(`❌ Topic extraction failed: ${res.status}`);
    }

    return await res.json();
}

// 📺 Search for YouTube videos by extracted topics
export async function fetchYouTubeVideos(topics) {
    const res = await fetch(`${BASE}/youtube/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(topics),
    });

    if (!res.ok) {
        throw new Error(`❌ YouTube scraping failed: ${res.status}`);
    }

    return await res.json();
}