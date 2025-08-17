import React from 'react';
import { Box, Tooltip } from '@mui/material';

interface PDFAnnotation {
  id: string;
  text: string;
  comment: string;
  pageNumber: number;
  coordinates: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  author: string;
  createdAt: string;
}

interface PDFAnnotationOverlayProps {
  annotations: PDFAnnotation[];
  pageNumber: number;
  scale: number;
  onAnnotationClick?: (annotation: PDFAnnotation) => void;
}

const PDFAnnotationOverlay: React.FC<PDFAnnotationOverlayProps> = ({
  annotations,
  pageNumber,
  scale,
  onAnnotationClick
}) => {
  // Filter annotations for this page
  const pageAnnotations = annotations.filter(ann => ann.pageNumber === pageNumber);

  if (pageAnnotations.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 10
      }}
    >
      {pageAnnotations.map((annotation) => {
        console.log('Rendering annotation overlay:', {
          id: annotation.id,
          coords: annotation.coordinates,
          scale: scale,
          finalPosition: {
            left: annotation.coordinates.x * scale,
            top: annotation.coordinates.y * scale,
            width: annotation.coordinates.width * scale,
            height: annotation.coordinates.height * scale
          }
        });
        
        return (
        <Tooltip
          key={annotation.id}
          title={
            <Box>
              <Box sx={{ fontWeight: 'bold', mb: 0.5 }}>
                {annotation.author}
              </Box>
              <Box>{annotation.comment}</Box>
              {annotation.text && annotation.text !== 'Document-level comment' && (
                <Box sx={{ mt: 0.5, fontStyle: 'italic', fontSize: '0.9em' }}>
                  "{annotation.text}"
                </Box>
              )}
            </Box>
          }
          placement="top"
          arrow
        >
          <Box
            sx={{
              position: 'absolute',
              left: annotation.coordinates.x * scale,
              top: annotation.coordinates.y * scale,
              width: annotation.coordinates.width * scale,
              height: annotation.coordinates.height * scale,
              bgcolor: 'rgba(255, 235, 59, 0.3)',
              border: '2px solid #FFC107',
              borderRadius: '2px',
              cursor: 'pointer',
              pointerEvents: 'auto',
              '&:hover': {
                bgcolor: 'rgba(255, 235, 59, 0.5)',
                borderColor: '#FF9800'
              }
            }}
            onClick={() => onAnnotationClick?.(annotation)}
          />
        </Tooltip>
        );
      })}
    </Box>
  );
};

export default PDFAnnotationOverlay;