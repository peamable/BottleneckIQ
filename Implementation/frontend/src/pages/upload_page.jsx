import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { FileUp, FileCheck, XCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/upload_file';

const fallbackStages = [
  { key: 'file_saved', label: 'File Saved', status: 'pending' },
  { key: 'cleaning', label: 'Cleaning', status: 'pending' },
  { key: 'staging', label: 'Staging', status: 'pending' },
  { key: 'validation', label: 'Validation', status: 'pending' },
  { key: 'ingestion', label: 'Ingestion', status: 'pending' },
  { key: 'aggregation', label: 'Aggregation', status: 'pending' },
  { key: 'analytics', label: 'Analytics', status: 'pending' },
];

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [lastUploadId, setLastUploadId] = useState(null);
  const [activeUploadId, setActiveUploadId] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [isContinuing, setIsContinuing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setPipelineStatus(null);
    setActiveUploadId(null);
    setModalOpen(false);
  };

  const removeFile = () => {
    setFile(null);
    setPipelineStatus(null);
    setActiveUploadId(null);
    setModalOpen(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const openFilePicker = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const handleStart = () => {
    setPipelineStatus({
      status: 'processing',
      message: 'Upload received. Starting pipeline.',
      stages: fallbackStages,
      validation_issues: [],
      missing_fields: [],
      allow_skip: false,
      skipped_rows: [],
      summary_report: null,
    });
    setModalOpen(true);
  };

  const handleAccepted = (payload) => {
    setLastUploadId(payload?.upload_id ?? null);
    setActiveUploadId(payload?.upload_id ?? null);
    setModalOpen(true);
  };

  const handleImmediateError = (err) => {
    console.error(err);
    const detail = err?.response?.data?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : detail?.message ||
          detail?.error ||
          err?.response?.data?.message ||
          err?.message ||
          'Upload failed. Please try again.';

    setPipelineStatus({
      status: 'failed',
      message,
      stages: fallbackStages,
      validation_issues: [],
      missing_fields: [],
      allow_skip: false,
      skipped_rows: [],
      summary_report: null,
    });
    setModalOpen(true);
  };

  useEffect(() => {
    if (!activeUploadId) return undefined;

    let intervalId;
    const fetchStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/upload-status/${activeUploadId}`);
        if (!response.ok) return;

        const payload = await response.json();
        setPipelineStatus(payload);
        setLastUploadId(payload.upload_id ?? activeUploadId);

        if (['completed', 'failed', 'action_required'].includes(payload.status)) {
          setActiveUploadId(null);
          if (intervalId) {
            window.clearInterval(intervalId);
          }
        }
      } catch (error) {
        console.error(error);
      }
    };

    fetchStatus();
    intervalId = window.setInterval(fetchStatus, 250);

    return () => window.clearInterval(intervalId);
  }, [activeUploadId]);

  const handleProcessAnyway = async () => {
    const targetUploadId = activeUploadId ?? pipelineStatus?.upload_id;
    if (!targetUploadId) return;

    setIsContinuing(true);
    try {
      await axios.post(`http://localhost:8000/upload/${targetUploadId}/process-anyway`);
      setPipelineStatus((current) => current ? {
        ...current,
        upload_id: targetUploadId,
        status: 'processing',
        message: 'Skipping invalid rows and resuming pipeline.',
        allow_skip: false,
      } : current);
      setActiveUploadId(targetUploadId);
    } catch (error) {
      console.error(error);
    } finally {
      setIsContinuing(false);
    }
  };

  const handleReplaceFromModal = () => {
    setModalOpen(false);
    openFilePicker();
  };

  const handleDragOver = (e) => {
    e.preventDefault();
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
    if (droppedFile) {
      setFile(droppedFile);
      setPipelineStatus(null);
      setActiveUploadId(null);
      setModalOpen(false);
    }
  };

  const renderStageIcon = (status) => {
    if (status === 'completed') return <CheckCircle2 size={18} className="stage-icon-complete" />;
    if (status === 'failed') return <span className="stage-badge failed">!</span>;
    if (status === 'in_progress') return <Loader2 size={18} className="stage-icon-spin" />;
    return <span className="stage-badge pending" />;
  };

  const stages = pipelineStatus?.stages ?? fallbackStages;
  const missingFields = pipelineStatus?.missing_fields ?? [];
  const validationIssues = pipelineStatus?.validation_issues ?? [];
  const summaryReport = pipelineStatus?.summary_report;
  const isActionRequired = pipelineStatus?.status === 'action_required';
  const isCompleted = pipelineStatus?.status === 'completed';
  const isFailed = pipelineStatus?.status === 'failed';
  // Keep the modal subtitle short when detailed validation issues are already shown below.
  const modalMessage = isActionRequired && (missingFields.length > 0 || validationIssues.length > 0)
    ? 'Review the issue below and choose how to continue.'
    : (pipelineStatus?.message || 'Calculating ED metrics and detecting bottlenecks.');

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2>Import ED Patient Data</h2>
        <p>Select a file to begin analysis.</p>

        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          hidden
          accept=".csv"
        />

        {!file ? (
          <label
            className={`drop-zone ${isDragging ? 'dragging' : ''}`}
            onClick={openFilePicker}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <FileUp size={48} className="icon-blue" />
            <span>Click or drag CSV file here</span>
          </label>
        ) : (
          <div className="file-preview">
            <FileCheck size={32} color="#10b981" />
            <div className="file-info">
              <span className="file-name">{file.name}</span>
              <span className="file-size">{(file.size / 1024).toFixed(2)} KB</span>
            </div>
            <div className="file-actions">
              <button
                type="button"
                onClick={openFilePicker}
                className="btn-secondary"
                aria-label="Replace file"
                title="Replace file"
              >
                <FileUp size={18} />
              </button>
              <button
                type="button"
                onClick={removeFile}
                className="btn-icon"
                aria-label="Remove file"
                title="Remove file"
              >
                <XCircle size={18} />
              </button>
            </div>
          </div>
        )}

        <FileUpload
          file={file}
          onUploadStart={handleStart}
          onUploadSuccess={handleAccepted}
          onUploadError={handleImmediateError}
          buttonLabel="Process Dataset"
        />
      </div>

      {modalOpen && (
        <div className="modal_overlay">
          <div className="modal_content modal_pipeline">
            <h3>
              {isCompleted
                ? 'Pipeline Complete'
                : isActionRequired
                  ? 'Pipeline Paused At Validation'
                  : 'Processing Pipeline'}
            </h3>
            <p>{modalMessage}</p>

            <div className="pipeline-stage-list">
              {stages.map((stage) => (
                <div key={stage.key} className={`pipeline-stage-row ${stage.status}`}>
                  <div className="pipeline-stage-status">
                    {renderStageIcon(stage.status)}
                  </div>
                  <div className="pipeline-stage-copy">
                    <span className="pipeline-stage-label">{stage.label}</span>
                    <span className="pipeline-stage-state">{stage.status.replace('_', ' ')}</span>
                  </div>
                </div>
              ))}
            </div>

            {missingFields.length > 0 && (
              <div className="pipeline-issue-box">
                <h4>Missing required fields</h4>
                <ul className="upload-error-list">
                  {missingFields.map((field) => (
                    <li key={field}>{field}</li>
                  ))}
                </ul>
              </div>
            )}

            {validationIssues.length > 0 && (
              <div className="pipeline-issue-box">
                <h4>Validation issues</h4>
                <ul className="upload-error-list">
                  {validationIssues.map((issue) => (
                    <li key={issue.code}>{issue.message}</li>
                  ))}
                </ul>
              </div>
            )}

            {!isCompleted && !!pipelineStatus?.skipped_rows?.length && (
              <div className="pipeline-issue-box pipeline-skip-box">
                <h4>Skipped rows</h4>
                <ul className="upload-error-list">
                  {pipelineStatus.skipped_rows.map((item) => (
                    <li key={item.code}>{item.rows_deleted} rows removed for {item.code}</li>
                  ))}
                </ul>
              </div>
            )}

            {isCompleted && summaryReport && (
              <div className="pipeline-summary-box">
                <h4>Pipeline summary</h4>
                <div className="pipeline-summary-grid">
                  <div className="pipeline-summary-item">
                    <span className="pipeline-summary-value">{summaryReport.stay_ids_inserted ?? 0}</span>
                    <span className="pipeline-summary-label">Stay IDs inserted</span>
                  </div>
                  <div className="pipeline-summary-item">
                    <span className="pipeline-summary-value">{summaryReport.rows_skipped_or_removed ?? 0}</span>
                    <span className="pipeline-summary-label">Rows skipped or removed</span>
                  </div>
                  <div className="pipeline-summary-item">
                    <span className="pipeline-summary-value">{summaryReport.ed_events_inserted ?? 0}</span>
                    <span className="pipeline-summary-label">ED events inserted</span>
                  </div>
                  <div className="pipeline-summary-item">
                    <span className="pipeline-summary-value">{summaryReport.stay_ids_summarized ?? 0}</span>
                    <span className="pipeline-summary-label">Stay IDs summarized</span>
                  </div>
                </div>
              </div>
            )}

            <div className="pipeline-actions">
              {isCompleted ? (
                <>
                  <button
                    className="btn_primary"
                    onClick={() => navigate('/view_metrics', { state: { upload_id: lastUploadId } })}
                  >
                    View Metrics Dashboard
                  </button>
                  <button className="btn-linkish" onClick={() => setModalOpen(false)}>
                    Close
                  </button>
                </>
              ) : isActionRequired ? (
                <div className="button-group">
                  <button className="btn-primary" onClick={handleReplaceFromModal}>
                    Fix Issue
                  </button>
                  {pipelineStatus?.allow_skip && (
                    <button
                      className="btn-process-anyway"
                      onClick={handleProcessAnyway}
                      disabled={isContinuing}
                    >
                      {isContinuing ? 'Resuming...' : 'Ignore & Continue'}
                    </button>
                  )}
                </div>
              ) : isFailed ? (
                <>
                  <button className="btn-primary" onClick={handleReplaceFromModal}>
                    Choose Another File
                  </button>
                  <button className="btn-linkish" onClick={() => setModalOpen(false)}>
                    Close
                  </button>
                </>
              ) : (
                <div className="pipeline-pending-note">The pipeline updates automatically as each stage completes.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
