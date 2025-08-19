import React, { useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import { 
  Box, 
  Typography, 
  Container,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import { Description } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../../services/api';

interface Document {
  id: number;
  title: string;
  filename: string;
  description: string;
  document_type: string;
  file_size: number;
  created_at: string;
  updated_at: string;
}

const DocumentList = forwardRef<{ refreshDocuments: () => void }>((props, ref) => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/documents');
      setDocuments(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useImperativeHandle(ref, () => ({
    refreshDocuments: fetchDocuments
  }));
  
  useEffect(() => {
    fetchDocuments();
  }, []);


  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
          All Documents
        </Typography>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && (
        <Grid container spacing={3}>
          {documents.map((document: Document) => (
            <Grid item xs={12} md={6} lg={4} key={document.id}>
              <Card 
                sx={{ 
                  height: '100%', 
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 4 }
                }}
                onClick={() => {
                  navigate(`/documents/${document.id}`);
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                    <Description sx={{ mr: 1, color: 'text.secondary' }} />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {document.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {document.description}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Chip 
                      label={document.document_type.toUpperCase()} 
                      size="small" 
                      variant="outlined" 
                    />
                    <Typography variant="caption" color="text.secondary">
                      {Math.round(document.file_size / 1024)} KB
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {!loading && !error && documents.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Description sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No documents found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload your first document to get started with annotations.
          </Typography>
        </Box>
        )}
      </Container>

    </Box>
  );
});

DocumentList.displayName = 'DocumentList';

export default DocumentList;