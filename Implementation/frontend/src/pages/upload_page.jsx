import React, { useState } from 'react';
import { FileUp, FileCheck, X, Loader2, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const UploadPage = () => {
  // 1. STATE: We use 'useState' to track if a file has been picked.
  // This allows the UI to change from "Upload" to "File Ready!"
  const [file, setFile] = useState(null);

  //  these will track the popup
  const [is_processing, set_is_processing] = useState(false);
  const [is_finished, set_is_finished] = useState(false);
  
  const navigate = useNavigate(); // Initialize navigation

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const removeFile = () => {
    setFile(null);
  };

  //  This handles the "Process" button click
  const handle_upload = () => {
    set_is_processing(true);
    set_is_finished(false);

    // Mocking the backend delay for 4 seconds. To be removed when we get response from backend
    setTimeout(() => {
      set_is_finished(true);
    }, 4000);
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2>Import ED Patient Data</h2>
        <p>Select a file to begin analysis.</p>

        {/* CONDITIONAL RENDERING: 
             If no file is selected, show the upload box.
             If a file exists, show the "File Selected" view. */}
        {!file ? (
          <label className="drop-zone">
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

        {/* THE ACTION BUTTON: Only "Ok" (Submit) if a file exists */}
        <button 
          className={`btn-primary ${!file ? 'disabled' : ''}`}
          disabled={!file}
          //onClick={() => alert("File sent to Backend ETL Pipeline!")}
          onClick={handle_upload}
        >
          Process Dataset
        </button>
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
                  onClick={() => navigate('/view_metrics')}
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