import React, { useState, useEffect } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Typography,
  Chip,
  Alert,
  TextField,
  InputAdornment
} from '@mui/material';
import { Delete, Search, Public, Lock } from '@mui/icons-material';
import api from '../../services/api';

interface Document {
  id: number;
  title: string;
  filename: string;
  file_type: string;
  key: string;
  date: string;
  owner_id: number;
  created_at: string;
  file_size: number;
  is_public: boolean;
}

const DocumentManagement: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredDocuments(documents);
    } else {
      const filtered = documents.filter(doc =>
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.key.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredDocuments(filtered);
    }
  }, [documents, searchQuery]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/documents/');
      setDocuments(response.data);
    } catch (error) {
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: number) => {
    if (window.confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      try {
        await api.delete(`/admin/documents/${documentId}/`);
        setSuccess('Document deleted successfully');
        loadDocuments();
      } catch (error: any) {
        setError(error.response?.data?.detail || 'Failed to delete document');
      }
    }
  };

  const handleTogglePublic = async (documentId: number) => {
    try {
      const response = await api.patch(`/admin/documents/${documentId}/toggle-public/`);
      setSuccess(response.data.message);
      loadDocuments();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to toggle document visibility');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Document Management</Typography>
        <TextField
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
          variant="outlined"
          size="small"
          sx={{ width: 300 }}
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Filename</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Key</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Owner ID</TableCell>
              <TableCell>Visibility</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDocuments.map((document) => (
              <TableRow key={document.id}>
                <TableCell>{document.title}</TableCell>
                <TableCell>{document.filename}</TableCell>
                <TableCell>
                  <Chip
                    label={document.file_type.toUpperCase()}
                    color="primary"
                    size="small"
                  />
                </TableCell>
                <TableCell>{document.key}</TableCell>
                <TableCell>{document.date}</TableCell>
                <TableCell>{formatFileSize(document.file_size)}</TableCell>
                <TableCell>{document.owner_id}</TableCell>
                <TableCell>
                  <Chip
                    label={document.is_public ? 'Public' : 'Private'}
                    color={document.is_public ? 'success' : 'default'}
                    size="small"
                    icon={document.is_public ? <Public /> : <Lock />}
                  />
                </TableCell>
                <TableCell>
                  {new Date(document.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <IconButton
                    color={document.is_public ? 'warning' : 'success'}
                    onClick={() => handleTogglePublic(document.id)}
                    title={document.is_public ? 'Make Private' : 'Make Public'}
                  >
                    {document.is_public ? <Lock /> : <Public />}
                  </IconButton>
                  <IconButton
                    color="error"
                    onClick={() => handleDeleteDocument(document.id)}
                    title="Delete Document"
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredDocuments.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body1" color="text.secondary">
            {searchQuery ? 'No documents match your search.' : 'No documents found.'}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default DocumentManagement;