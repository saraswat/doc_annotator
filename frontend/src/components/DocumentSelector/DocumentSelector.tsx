import React from 'react';
import { Box, Typography } from '@mui/material';
import { Description } from '@mui/icons-material';

const DocumentSelector: React.FC = () => {
  return (
    <Box sx={{ 
      flex: 1, 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      p: 4 
    }}>
      <Box sx={{ textAlign: 'center', maxWidth: 400 }}>
        <Description sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h5" color="text.secondary" gutterBottom>
          Select a Document
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Choose a document from the sidebar to view and annotate it.
        </Typography>
      </Box>
    </Box>
  );
};

export default DocumentSelector;