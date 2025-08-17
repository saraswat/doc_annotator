import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Button
} from '@mui/material';
import { Add, CloudUpload } from '@mui/icons-material';
import apiService from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import BulkUploadDialog from '../Upload/BulkUploadDialog';
import SingleUploadDialog from '../Upload/SingleUploadDialog';

interface Document {
  id: number;
  title: string;
  description: string;
  document_type: string;
  file_size: number;
}

interface MainLayoutProps {
  children: React.ReactNode;
  currentDocumentId?: string;
  onUploadComplete?: () => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children, currentDocumentId, onUploadComplete }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [keys, setKeys] = useState<string[]>([]);
  const [dates, setDates] = useState<string[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedKey, setSelectedKey] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bulkUploadOpen, setBulkUploadOpen] = useState(false);
  const [singleUploadOpen, setSingleUploadOpen] = useState(false);

  // Load available keys on component mount
  useEffect(() => {
    if (!user) return;

    const fetchKeys = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiService.get('/documents/keys');
        
        const keysArray = Array.isArray(response.data) 
          ? response.data.filter(key => typeof key === 'string' && key.trim() !== '')
          : [];
        
        setKeys(keysArray);
      } catch (err: any) {
        setError('Failed to load document keys');
        setKeys([]);
      } finally {
        setLoading(false);
      }
    };

    fetchKeys();
  }, [user]);

  // Load dates when a key is selected
  useEffect(() => {
    const fetchDates = async () => {
      if (!user || !selectedKey) {
        setDates([]);
        setSelectedDate('');
        setDocuments([]);
        return;
      }

      try {
        setLoading(true);
        const response = await apiService.get(`/documents/dates?key=${encodeURIComponent(selectedKey)}`);
        
        const datesArray = Array.isArray(response.data) 
          ? response.data.filter(date => typeof date === 'string' && date.trim() !== '')
          : [];
        
        setDates(datesArray);
        setSelectedDate('');
        setDocuments([]);
        setError(null);
      } catch (err: any) {
        setError('Failed to load dates');
        setDates([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDates();
  }, [user, selectedKey]);

  // Load documents when both key and date are selected
  useEffect(() => {
    const fetchDocuments = async () => {
      if (!user || !selectedKey || !selectedDate) {
        setDocuments([]);
        return;
      }

      try {
        setLoading(true);
        const response = await apiService.get(
          `/documents/by-key-date?key=${encodeURIComponent(selectedKey)}&date=${encodeURIComponent(selectedDate)}`
        );
        
        const documentsArray = Array.isArray(response.data) ? response.data : [];
        setDocuments(documentsArray);
        setError(null);
        
        // Only auto-navigate if there's exactly one document
        if (documentsArray.length === 1) {
          const firstDocument = documentsArray[0];
          navigate(`/documents/${firstDocument.id}`, { replace: true });
        }
      } catch (err: any) {
        setError('Failed to load documents');
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [user, selectedKey, selectedDate, navigate]);

  const handleKeyChange = (event: any) => {
    setSelectedKey(event.target.value);
  };

  const handleDateChange = (event: any) => {
    setSelectedDate(event.target.value);
  };

  const handleDocumentClick = (documentId: number) => {
    navigate(`/documents/${documentId}`);
  };

  const handleBulkUploadComplete = () => {
    // Refresh the current data
    if (selectedKey) {
      const fetchKeys = async () => {
        try {
          const response = await apiService.get('/documents/keys');
          const keysArray = Array.isArray(response.data) 
            ? response.data.filter(key => typeof key === 'string' && key.trim() !== '')
            : [];
          setKeys(keysArray);
        } catch (err) {
          console.error('Failed to refresh keys after upload');
        }
      };
      fetchKeys();
    }
    
    // Call the child component's refresh if provided
    onUploadComplete?.();
  };

  const handleSingleUploadComplete = () => {
    // Refresh the current data
    if (selectedKey) {
      const fetchKeys = async () => {
        try {
          const response = await apiService.get('/documents/keys');
          const keysArray = Array.isArray(response.data) 
            ? response.data.filter(key => typeof key === 'string' && key.trim() !== '')
            : [];
          setKeys(keysArray);
        } catch (err) {
          console.error('Failed to refresh keys after upload');
        }
      };
      fetchKeys();
    }
    
    // Call the child component's refresh if provided
    onUploadComplete?.();
  };

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex' }}>
      {/* Left Sidebar - Key-Date Selector and Controls */}
      <Box sx={{ 
        width: 300, 
        borderRight: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        display: 'flex',
        flexDirection: 'column',
        p: 2
      }}>
        <Typography variant="h5" gutterBottom>
          Document Browser
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Select key and date to filter documents
        </Typography>

        {/* Key-Date Selection */}
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Document Key</InputLabel>
          <Select
            value={selectedKey}
            label="Document Key"
            onChange={handleKeyChange}
            disabled={loading}
            size="small"
          >
            {keys.map((key, index) => (
              <MenuItem key={`key-${index}`} value={String(key)}>
                {String(key)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Document Date</InputLabel>
          <Select
            value={selectedDate}
            label="Document Date"
            onChange={handleDateChange}
            disabled={!selectedKey || loading}
            size="small"
          >
            {dates.map((date, index) => (
              <MenuItem key={`date-${index}`} value={String(date)}>
                {String(date)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Loading Indicator */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <CircularProgress size={20} />
          </Box>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2, fontSize: '0.8rem' }}>
            {typeof error === 'string' ? error : JSON.stringify(error)}
          </Alert>
        )}

        {/* Document List */}
        <Box sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
          {!loading && selectedKey && selectedDate && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                {documents.length} document{documents.length !== 1 ? 's' : ''} for {selectedKey} - {selectedDate}
              </Typography>
              
              {documents.length === 0 ? (
                <Alert severity="info" sx={{ fontSize: '0.8rem' }}>
                  No documents found for this combination.
                </Alert>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {documents.map((doc) => (
                    <Card 
                      key={doc.id}
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { boxShadow: 2 },
                        border: doc.id === parseInt(currentDocumentId || '0') ? '2px solid' : '1px solid',
                        borderColor: doc.id === parseInt(currentDocumentId || '0') ? 'primary.main' : 'divider'
                      }}
                      onClick={() => handleDocumentClick(doc.id)}
                    >
                      <CardContent sx={{ p: 1.5 }}>
                        <Typography variant="body2" fontWeight="medium" gutterBottom>
                          {String(doc.title || 'Untitled')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                          {String(doc.description || '').substring(0, 60)}
                          {(doc.description || '').length > 60 ? '...' : ''}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          <Chip 
                            label={String(doc.document_type || 'unknown').toUpperCase()} 
                            size="small" 
                            variant="outlined"
                            sx={{ fontSize: '0.65rem', height: '18px' }}
                          />
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                            {Math.round((doc.file_size || 0) / 1024)} KB
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </>
          )}

          {/* Instructions when no selection is made */}
          {!loading && !selectedKey && (
            <Alert severity="info" sx={{ fontSize: '0.8rem' }}>
              Select a document key to see available dates.
            </Alert>
          )}

          {!loading && selectedKey && !selectedDate && (
            <Alert severity="info" sx={{ fontSize: '0.8rem' }}>
              Select a date to see documents for {selectedKey}.
            </Alert>
          )}
        </Box>

        {/* Upload Controls */}
        <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Upload Documents
          </Typography>
          <Button
            variant="outlined"
            size="small"
            fullWidth
            startIcon={<CloudUpload />}
            onClick={() => setBulkUploadOpen(true)}
            sx={{ mb: 1 }}
          >
            Bulk Upload
          </Button>
          <Button
            variant="contained"
            size="small"
            fullWidth
            startIcon={<Add />}
            onClick={() => setSingleUploadOpen(true)}
          >
            Upload Document
          </Button>
        </Box>

        {/* Bottom Controls */}
        <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 2, mt: 'auto' }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Welcome, {user?.name}
          </Typography>
          <Button
            variant="outlined"
            size="small"
            fullWidth
            onClick={logout}
            sx={{ mb: 1 }}
          >
            Sign Out
          </Button>
          <Button
            variant="text"
            size="small"
            fullWidth
            onClick={() => navigate('/documents')}
          >
            View All Documents
          </Button>
        </Box>
      </Box>

      {/* Main Content Area */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {children}
      </Box>

      {/* Bulk Upload Dialog */}
      <BulkUploadDialog
        open={bulkUploadOpen}
        onClose={() => setBulkUploadOpen(false)}
        onUploadComplete={handleBulkUploadComplete}
      />

      {/* Single Upload Dialog */}
      <SingleUploadDialog
        open={singleUploadOpen}
        onClose={() => setSingleUploadOpen(false)}
        onUploadComplete={handleSingleUploadComplete}
      />
    </Box>
  );
};

export default MainLayout;