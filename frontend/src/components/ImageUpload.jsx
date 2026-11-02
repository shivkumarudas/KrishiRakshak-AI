import React, { useState, useRef } from 'react';
import { Upload, X, Image as ImageIcon, AlertCircle } from 'lucide-react';

const MAX_SIZE_MB = 10;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

/**
 * Reusable Image Upload & Preview Component.
 * Enforces file format and size limits before emitting to caller.
 */
export default function ImageUpload({ onFileSelect, onClear, selectedFile, disabled = false }) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const validateAndEmit = (file) => {
    setError('');
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      setError(`Unsupported file format (${file.type || 'unknown'}). Please upload a JPEG, PNG, or WebP photo.`);
      return;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Image exceeds ${MAX_SIZE_MB} MB limit (${(file.size / (1024 * 1024)).toFixed(2)} MB). Please select a smaller photo.`);
      return;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    onFileSelect(file, url);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    validateAndEmit(file);
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    validateAndEmit(file);
  };

  const handleClear = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (onClear) {
      onClear();
    }
  };

  return (
    <div className="image-upload-component">
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1rem' }} role="alert">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {!previewUrl && !selectedFile ? (
        <div
          onClick={() => !disabled && fileInputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          tabIndex={disabled ? -1 : 0}
          role="button"
          onKeyDown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          style={{
            border: dragOver ? '2px dashed var(--primary-color)' : '2px dashed var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            backgroundColor: dragOver ? 'var(--bg-leaf)' : 'var(--bg-page)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            opacity: disabled ? 0.6 : 1,
          }}
          aria-label="Upload crop image"
        >
          <input
            type="file"
            ref={fileInputRef}
            accept="image/jpeg,image/png,image/webp"
            style={{ display: 'none' }}
            onChange={handleChange}
            disabled={disabled}
          />
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                backgroundColor: 'var(--bg-leaf)',
                color: 'var(--primary-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Upload size={26} />
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '1rem', marginBottom: '0.25rem' }}>
                Click to browse or drag and drop crop photo
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Supports JPEG, PNG, WebP up to {MAX_SIZE_MB} MB
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div
          style={{
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '1rem',
            backgroundColor: '#ffffff',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary-dark)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <ImageIcon size={16} /> Selected Photo: {selectedFile?.name || 'crop_image.jpg'}
            </span>
            <button
              type="button"
              onClick={handleClear}
              className="btn btn-secondary"
              style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
              aria-label="Remove image"
            >
              <X size={14} /> Remove Photo
            </button>
          </div>

          {previewUrl && (
            <div
              style={{
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                maxHeight: '320px',
                backgroundColor: '#000000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img
                src={previewUrl}
                alt="Uploaded crop preview"
                style={{
                  maxHeight: '320px',
                  maxWidth: '100%',
                  objectFit: 'contain',
                }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
