import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Paper,
  ToggleButtonGroup,
  ToggleButton,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  CloudUpload,
  Folder,
  Description,
  CheckCircle,
  Error,
  Warning,
  Archive
} from '@mui/icons-material';
// import { useDropzone } from 'react-dropzone';
import apiService from '../../services/api';

interface BulkUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUploadComplete: () => void;
}

interface UploadStatus {
  file: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  message?: string;
  key?: string;
  date?: string;
}

const BulkUploadDialog: React.FC<BulkUploadDialogProps> = ({
  open,
  onClose,
  onUploadComplete
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [uploadMode, setUploadMode] = useState<'file' | 'directory'>('file');
  const [uploading, setUploading] = useState(false);
  const [makePublic, setMakePublic] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Update input attributes when mode changes
  useEffect(() => {
    if (fileInputRef.current) {
      const input = fileInputRef.current;
      if (uploadMode === 'directory') {
        (input as any).webkitdirectory = true;
        input.removeAttribute('accept');
        input.multiple = true;
      } else {
        (input as any).webkitdirectory = false;
        input.setAttribute('accept', '.zip,.tar,.tar.gz,.tgz');
        input.multiple = false;
        // Reset the input when switching modes
        input.value = '';
      }
    }
  }, [uploadMode]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    if (uploadMode === 'directory') {
      setSelectedFiles(files);
      setSelectedFile(null);
      setError(null);
      setUploadStatus([]);
    } else {
      const file = files[0];
      if (file) {
        const extension = file.name.toLowerCase().split('.').pop();
        
        if (extension === 'zip' || extension === 'tar' || extension === 'gz' || extension === 'tgz') {
          setSelectedFile(file);
          setSelectedFiles(null);
          setError(null);
          setUploadStatus([]);
        } else {
          setError('Please select a ZIP or TAR file');
        }
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile && !selectedFiles) return;

    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setUploadStatus([]);

    try {
      const formData = new FormData();
      
      // Add public flag
      formData.append('make_public', makePublic.toString());
      
      if (uploadMode === 'file' && selectedFile) {
        formData.append('file', selectedFile);
      } else if (uploadMode === 'directory' && selectedFiles) {
        // For directory upload, we need to send all files with their relative paths
        Array.from(selectedFiles).forEach((file) => {
          formData.append('files', file);
          // Store the relative path from the webkitRelativePath
          formData.append('paths', file.webkitRelativePath || file.name);
        });
      }

      const endpoint = uploadMode === 'file' ? '/documents/bulk-upload' : '/documents/bulk-upload-directory';
      const response = await apiService.post(endpoint, formData, {
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

      // Handle the response which should contain status for each processed file
      if (response.data.results) {
        setUploadStatus(response.data.results);
        
        const successCount = response.data.results.filter(
          (result: UploadStatus) => result.status === 'success'
        ).length;
        
        if (successCount > 0) {
          onUploadComplete();
        }
      }

      if (response.data.errors && response.data.errors.length > 0) {
        setError(`Some files failed to upload: ${response.data.errors.join(', ')}`);
      }

    } catch (err: any) {
      console.error('Bulk upload error:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to upload files'
      );
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setSelectedFile(null);
      setSelectedFiles(null);
      setUploadStatus([]);
      setError(null);
      setUploadProgress(0);
      setMakePublic(false);
      onClose();
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle color="success" />;
      case 'error':
        return <Error color="error" />;
      case 'uploading':
        return <CloudUpload color="primary" />;
      default:
        return <Description color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success.main';
      case 'error':
        return 'error.main';
      case 'uploading':
        return 'primary.main';
      default:
        return 'text.disabled';
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '400px' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CloudUpload />
          Bulk Document Upload
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Choose upload method:
            </Typography>
            <ToggleButtonGroup
              value={uploadMode}
              exclusive
              onChange={(event, newMode) => {
                if (newMode) {
                  setUploadMode(newMode);
                  setSelectedFile(null);
                  setSelectedFiles(null);
                  setError(null);
                }
              }}
              size="small"
            >
              <ToggleButton value="file">
                <Archive sx={{ mr: 1 }} />
                Archive File (ZIP/TAR)
              </ToggleButton>
              <ToggleButton value="directory">
                <Folder sx={{ mr: 1 }} />
                Directory
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {uploadMode === 'file' 
              ? 'Upload a ZIP or TAR file containing documents organized in the following structure:'
              : 'Select a directory containing documents organized in the following structure:'
            }
          </Typography>
          
          <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 3 }}>
            <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', fontSize: '0.9em' }}>
{`archive.zip/
├── key1/
│   ├── 2023/
│   │   ├── document1.pdf
│   │   └── document2.html
│   └── 2024/
│       └── document3.md
└── key2/
    └── 2024/
        └── document4.txt`}
            </Typography>
          </Paper>
          
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2" component="div">
              • Each document will be assigned the <strong>key</strong> from its folder name<br />
              • The <strong>date</strong> will be extracted from the subfolder name<br />
              • Supported formats: PDF, HTML, Markdown, and Text files<br />
              • Document titles will be generated from filenames
            </Typography>
          </Alert>
          
          {/* Public Documents Option */}
          <Box sx={{ mb: 3 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={makePublic}
                  onChange={(e) => setMakePublic(e.target.checked)}
                  disabled={uploading}
                />
              }
              label={
                <Box>
                  <Typography variant="body2" component="span">
                    Make documents public
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Public documents can be viewed by all users without restrictions
                  </Typography>
                </Box>
              }
            />
          </Box>
        </Box>

        {/* File Selection */}
        <Box
          sx={{
            border: 2,
            borderColor: 'grey.300',
            borderStyle: 'dashed',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            bgcolor: 'grey.50',
            mb: 3,
            opacity: uploading ? 0.6 : 1
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            disabled={uploading}
            style={{ display: 'none' }}
            id="bulk-upload-input"
          />
          
          {selectedFile || selectedFiles ? (
            <Box>
              {uploadMode === 'file' ? (
                <Archive sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              ) : (
                <Folder sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              )}
              <Typography variant="h6" gutterBottom>
                {selectedFile 
                  ? selectedFile.name 
                  : `${selectedFiles?.length} files selected`
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedFile 
                  ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB`
                  : selectedFiles 
                    ? `${(Array.from(selectedFiles).reduce((total, file) => total + file.size, 0) / (1024 * 1024)).toFixed(2)} MB total`
                    : ''
                }
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setSelectedFile(null);
                  setSelectedFiles(null);
                }}
                disabled={uploading}
                sx={{ mt: 1 }}
              >
                Choose Different {uploadMode === 'file' ? 'File' : 'Directory'}
              </Button>
            </Box>
          ) : (
            <Box>
              {uploadMode === 'file' ? (
                <Archive sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
              ) : (
                <Folder sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
              )}
              <Typography variant="h6" gutterBottom>
                {uploadMode === 'file' ? 'Select a ZIP or TAR file' : 'Select a directory'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {uploadMode === 'file' ? 'Click below to choose a file' : 'Click below to choose a directory'}
              </Typography>
              <Button
                variant="contained"
                component="label"
                htmlFor="bulk-upload-input"
                disabled={uploading}
                startIcon={uploadMode === 'file' ? <Archive /> : <Folder />}
              >
                {uploadMode === 'file' ? 'Choose File' : 'Choose Directory'}
              </Button>
            </Box>
          )}
        </Box>

        {/* Upload Progress */}
        {uploading && (
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" sx={{ flex: 1 }}>
                Uploading and processing files...
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

        {/* Upload Status */}
        {uploadStatus.length > 0 && (
          <Box>
            <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
              Upload Results:
            </Typography>
            <List dense>
              {uploadStatus.map((status: UploadStatus, index: number) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      {getStatusIcon(status.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={status.file}
                      secondary={
                        <Box>
                          {status.key && status.date && (
                            <Typography variant="caption" color="text.secondary">
                              Key: {status.key} • Date: {status.date}
                            </Typography>
                          )}
                          {status.message && (
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                display: 'block',
                                color: getStatusColor(status.status)
                              }}
                            >
                              {status.message}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < uploadStatus.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Box>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={uploading}>
          {uploadStatus.length > 0 ? 'Close' : 'Cancel'}
        </Button>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={(!selectedFile && !selectedFiles) || uploading}
          startIcon={uploading ? undefined : <CloudUpload />}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BulkUploadDialog;