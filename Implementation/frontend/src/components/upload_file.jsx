import React, { useState } from 'react';
import axios from 'axios';

const FileUpload = ({ file, onUploadStart, onUploadSuccess, onUploadError }) => {
 
  const [status, setStatus] = useState('initial'); // initial 
  
  // move from upload_page file

  const handle_upload = async () => {
    if (!file) return;

    setStatus('uploading');
    onUploadStart?.();

    const formData = new FormData();
    formData.append('file', file);

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
          className={`btn-primary ${!file ? 'disabled' : ''}`}
          disabled={!file}
          //onClick={() => alert("File sent to Backend ETL Pipeline!")}
          onClick={handle_upload}
        >
          Process Dataset
        </button>
    </div>
        
  );
};

export default FileUpload;
