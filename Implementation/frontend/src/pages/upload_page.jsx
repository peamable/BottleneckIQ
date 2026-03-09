import React, { useState } from 'react';
import { FileUp, FileCheck, X, Loader2, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/upload_file';

const UploadPage = () => {
  // 1. STATE: We use 'useState' to track if a file has been picked.
  // This allows the UI to change from "Upload" to "File Ready!"
  const [file, setFile] = useState(null);

  //  these will track the popup
  const [is_processing, set_is_processing] = useState(false);
  const [is_finished, set_is_finished] = useState(false);
  const [lastUploadId, setLastUploadId] = useState(null);
  
  const navigate = useNavigate(); // Initialize navigation

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const removeFile = () => {
    setFile(null);
  };

  //  handle_upload move to upload_file

  const handleStart = () => {
    set_is_processing(true);
    set_is_finished(false);
  };

  const handleSuccess = (payload) => {
    setLastUploadId(payload?.upload_id ?? null);
    set_is_finished(true);
  };

  const handleError = (err) => {
    console.error(err);
    set_is_processing(false);
    set_is_finished(false);
  };

  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault(); // required, otherwise drop is blocked
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

  const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) setFile(droppedFile);
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2>Import ED Patient Data</h2>
        <p>Select a file to begin analysis.</p>

        {/* CONDITIONAL RENDERING: 
             If no file is selected, show the upload box.
             If a file exists, show the "File Selected" view.
             --- EDITED DROP ZONE ---- */}
        {!file ? (
          <label 
            className={`drop-zone ${isDragging ? 'dragging': ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <FileUp size={48} className="icon-blue" />
            <span>Click or drag CSV file here</span>
            <input type="file" onChange={handleFileChange} hidden accept=".csv" />
          </label>
        ) : (
          <div className="file-preview">
            <FileCheck size={32} color="#10b981" />
            <div className="file-info">
              <span className="file-name">{file.name}</span>
              <span className="file-size">{(file.size / 1024).toFixed(2)} KB</span>
            </div>
            <button onClick={removeFile} className="btn-icon">
              <X size={20} />
            </button>
          </div>
        )}

        <FileUpload
          file={file}
          onUploadStart={handleStart}
          onUploadSuccess={handleSuccess}
          onUploadError={handleError}
        />       

        {/* THE ACTION BUTTON part move to upload_file */}
      </div>

     {is_processing && (
        <div className="modal_overlay">
          <div className="modal_content">
            {!is_finished ? (
              <>
                <Loader2 size={48} className="spinner" />
                <h3>Processing Pipeline...</h3>
                <p>Calculating ED metrics and detecting bottlenecks.</p>
                <div className="progress_bar_container">
                  <div className="progress_bar_fill"></div>
                </div>
              </>
            ) : (
              <>
                <CheckCircle2 size={48} color="#10b981" />
                <h3>Analysis Complete!</h3>
                <p>Metrics have been successfully calculated.</p>
                <button 
                  className="btn_primary" 
                  onClick={() => navigate('/view_metrics', { state: { upload_id: lastUploadId } })}
                >
                  View Metrics Dashboard
                </button>
              </>
            )}
          </div> 
          </div>
      )}
    </div>
  );
};

export default UploadPage;
