import React, { useState } from 'react';
import FileUpload from './components/FileUpload.jsx';
import NotesViewer from './components/NotesViewer.jsx';
import TopicPanel from './components/TopicPanel.jsx';
import YouTubeResults from './components/YouTubeResults.jsx';

function App() {
  const [notes, setNotes] = useState('');
  const [topics, setTopics] = useState([]);
  const [videos, setVideos] = useState([]);

  return (
    <div className="container">
      <h1>StudyApp</h1>
      <FileUpload onNotesGenerated={setNotes} />
      <NotesViewer notes={notes} />
      {notes && <TopicPanel notes={notes} onTopicsExtracted={setTopics} />}
      {topics.length > 0 && (
        <YouTubeResults topics={topics} setVideos={setVideos} />
      )}
    </div>
  );
}

export default App;