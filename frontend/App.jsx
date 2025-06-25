import React from 'react';
import FileUpload from './components/FileUpload';
import NotesViewer from './components/NotesViewer';

function App() {
  return (
    <div className="app-container">
      <h1>Study Assistant</h1>
      <FileUpload />
      <NotesViewer />
    </div>
  );
}

export default App;