import React, { useState, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  Alert,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  Error
} from '@mui/icons-material';
import apiService from '../../services/api';

interface SingleUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUploadComplete: () => void;
}

const SingleUploadDialog: React.FC<SingleUploadDialogProps> = ({
  open,
  onClose,
  onUploadComplete
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentKey, setDocumentKey] = useState<string>('');
  const [documentDate, setDocumentDate] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      setSuccess(false);
      
      // Auto-generate title from filename if not already set
      if (!title) {
        const filename = file.name;
        const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.')) || filename;
        const autoTitle = nameWithoutExt.replace(/[_-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        setTitle(autoTitle);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !documentKey || !documentDate || !title) {
      setError('Please fill in all required fields');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', title);
      formData.append('description', description);
      formData.append('document_key', documentKey);
      formData.append('document_date', documentDate);

      const response = await apiService.post('/documents/upload-single/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: any) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setUploadProgress(percentCompleted);
        }
      });

      setSuccess(true);
      onUploadComplete();
      
      // Reset form after successful upload
      setTimeout(() => {
        handleClose();
      }, 1500);

    } catch (err: any) {
      console.error('Upload error:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to upload document'
      );
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setSelectedFile(null);
      setDocumentKey('');
      setDocumentDate('');
      setTitle('');
      setDescription('');
      setError(null);
      setSuccess(false);
      setUploadProgress(0);
      onClose();
    }
  };

  const isFormValid = selectedFile && documentKey && documentDate && title;

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { minHeight: '500px' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CloudUpload />
          Upload Document
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {/* File Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Select Document File
          </Typography>
          
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            disabled={uploading}
            style={{ display: 'none' }}
            accept=".pdf,.html,.htm,.md,.markdown,.txt"
            id="single-upload-input"
          />
          
          {selectedFile ? (
            <Box sx={{ 
              p: 2, 
              border: 1, 
              borderColor: 'success.main', 
              borderRadius: 1, 
              bgcolor: 'success.50' 
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Description color="success" />
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    {selectedFile.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                sx={{ mt: 1 }}
              >
                Choose Different File
              </Button>
            </Box>
          ) : (
            <Box sx={{
              border: 2,
              borderColor: 'grey.300',
              borderStyle: 'dashed',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              bgcolor: 'grey.50'
            }}>
              <Description sx={{ fontSize: 40, color: 'text.disabled', mb: 1 }} />
              <Typography variant="body2" gutterBottom>
                PDF, HTML, Markdown, or Text files
              </Typography>
              <Button
                variant="contained"
                component="label"
                htmlFor="single-upload-input"
                disabled={uploading}
                startIcon={<CloudUpload />}
              >
                Choose File
              </Button>
            </Box>
          )}
        </Box>

        {/* Document Key and Date */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Document Classification
          </Typography>
          
          <TextField
            fullWidth
            label="Document Key"
            value={documentKey}
            onChange={(e) => setDocumentKey(e.target.value)}
            disabled={uploading}
            placeholder="e.g., AAPL, GOOGL, TSLA"
            sx={{ mb: 2 }}
            required
          />
          
          <TextField
            fullWidth
            label="Document Date"
            value={documentDate}
            onChange={(e) => setDocumentDate(e.target.value)}
            disabled={uploading}
            placeholder="e.g., 2024, 2023-Q4, 2024-Q1"
            required
          />
        </Box>

        {/* Document Metadata */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Document Details
          </Typography>
          
          <TextField
            fullWidth
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={uploading}
            placeholder="Document title"
            sx={{ mb: 2 }}
            required
          />
          
          <TextField
            fullWidth
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={uploading}
            placeholder="Optional description"
            multiline
            rows={2}
          />
        </Box>

        {/* Upload Progress */}
        {uploading && (
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" sx={{ flex: 1 }}>
                Uploading document...
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {uploadProgress}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={uploadProgress}
              sx={{ mb: 2 }}
            />
          </Box>
        )}

        {/* Success Message */}
        {success && (
          <Alert 
            severity="success" 
            sx={{ mb: 2 }}
            icon={<CheckCircle />}
          >
            Document uploaded successfully!
          </Alert>
        )}

        {/* Error Display */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
            icon={<Error />}
          >
            {error}
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={uploading}>
          {success ? 'Close' : 'Cancel'}
        </Button>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!isFormValid || uploading}
          startIcon={uploading ? undefined : <CloudUpload />}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SingleUploadDialog;