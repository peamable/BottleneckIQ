import React, { useState } from 'react';
import axios from 'axios';

const FileUpload = ({
  file,
  onUploadStart,
  onUploadSuccess,
  onUploadError,
  buttonLabel = 'Process Dataset',
  skipInvalidRows = false,
  buttonClassName = 'btn-primary',
}) => {
 
  const [status, setStatus] = useState('initial'); // initial 
  
  // move from upload_page file

  const handle_upload = async () => {
    if (!file) return;

    setStatus('uploading');
    onUploadStart?.();

    const formData = new FormData();
    formData.append('file', file);
    // This allows the retry action to ask the backend to drop skippable invalid rows.
    formData.append('skip_invalid_rows', skipInvalidRows ? 'true' : 'false');

    try {
      const res = await axios.post('http://localhost:8000/upload', formData);

      if (res.status === 200) {
        setStatus('success');
        onUploadSuccess?.(res.data);
      } else {
        setStatus('fail');
        onUploadError?.(new Error('Non-200 response'));
      }
    } catch (err) {
      setStatus('fail');
      onUploadError?.(err);
    }
  };

  return (
    <div>
        {/* move from upload_page file
            THE ACTION BUTTON: Only "Ok" (Submit) if a file exists */}
        <button 
          className={`${buttonClassName} ${!file ? 'disabled' : ''}`}
          disabled={!file}
          //onClick={() => alert("File sent to Backend ETL Pipeline!")}
          onClick={handle_upload}
        >
          {buttonLabel}
        </button>
    </div>
        
  );
};

export default FileUpload;
