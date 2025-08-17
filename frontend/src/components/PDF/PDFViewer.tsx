import React, { useState, useEffect } from 'react';
import { PdfViewer, NormalizedTextSelection, TextSelectionWithCSSProperties } from 'react-pdf-selection';
import axios from 'axios';
import { Box, IconButton, Typography, Alert, CircularProgress } from '@mui/material';
import { ZoomIn, ZoomOut } from '@mui/icons-material';
import 'react-pdf-selection/style/react_pdf_viewer.css';

// Enhanced highlight styles
const highlightStyles = `
  .pdf-highlight-enhanced {
    animation: highlightPulse 2s ease-in-out;
  }
  
  .pdf-highlight-enhanced::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, rgba(255, 235, 59, 0.3), rgba(255, 193, 7, 0.5));
    border-radius: 5px;
    z-index: -1;
  }
  
  @keyframes highlightPulse {
    0% { 
      background-color: rgba(33, 150, 243, 0.9);
      box-shadow: 0 0 25px rgba(33, 150, 243, 0.7);
    }
    50% { 
      background-color: rgba(255, 235, 59, 0.9);
      box-shadow: 0 0 20px rgba(255, 235, 59, 0.7);
    }
    100% { 
      background-color: rgba(255, 235, 59, 0.9);
      box-shadow: 0 3px 12px rgba(255, 111, 0, 0.6);
    }
  }
`;

// Inject enhanced styles
const injectHighlightStyles = () => {
  if (typeof window !== 'undefined' && !window.document.getElementById('pdf-highlight-styles')) {
    const styleSheet = window.document.createElement('style');
    styleSheet.id = 'pdf-highlight-styles';
    styleSheet.innerHTML = highlightStyles;
    window.document.head.appendChild(styleSheet);
  }
};

interface PDFViewerProps {
  url: string;
  annotations?: any[];
  onTextSelection?: (selection: {
    text: string;
    pageNumber: number;
    coordinates: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }) => void;
  onAnnotationClick?: (annotation: any) => void;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ url, annotations = [], onTextSelection, onAnnotationClick }) => {
  const [scale, setScale] = useState<number>(0.8);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pdfData, setPdfData] = useState<string | null>(null);

  // Inject enhanced styles on mount
  useEffect(() => {
    injectHighlightStyles();
  }, []);

  // Convert our annotations to react-pdf-selection format
  
  const selectionAnnotations: TextSelectionWithCSSProperties<any>[] = annotations
    .filter(ann => ann.coordinates && ann.pageNumber && 
      !isNaN(ann.coordinates.x) && !isNaN(ann.coordinates.y) && 
      !isNaN(ann.coordinates.width) && !isNaN(ann.coordinates.height))
    .map(ann => {
      
      // Check if coordinates are already in percentage format or decimal
      const rawX = ann.coordinates.x;
      const rawY = ann.coordinates.y;
      const rawWidth = ann.coordinates.width;
      const rawHeight = ann.coordinates.height;
      
      
      // Use coordinates as-is since they're already in 0-1 normalized range
      const coords = {
        x: Number(rawX),      
        y: Number(rawY),      
        width: Number(rawWidth),   
        height: Number(rawHeight)  
      };
      
      
      const vvv = {
        id: ann.id,
        text: ann.text,
        comment: ann.comment,
        author: ann.author,
        pageNumber: ann.pageNumber, // Add pageNumber to top level
        position: {
          pageNumber: ann.pageNumber,
          boundingRect: {
            left: coords.x,           
            top: coords.y,            
            right: coords.x + coords.width,      
            bottom: coords.y + coords.height   
          },
          rects: ann.coordinates.rects ? ann.coordinates.rects : [{
            left: coords.x,
            top: coords.y,
            right: coords.x + coords.width,
            bottom: coords.y + coords.height
          }]
        }
      };
      return vvv;
    });


  // Fetch PDF data with authentication
  useEffect(() => {
    
    const fetchPdfData = async () => {
      if (!url) {
        return;
      }
      
      try {
        setIsLoading(true);
        setError(null);
        
        // Extract document ID from URL  
        const urlMatch = url.match(/\/documents\/(\d+)\/pdf/);
        if (!urlMatch) {
          setError('Invalid PDF URL');
          return;
        }
        
        const documentId = urlMatch[1];
        
        const API_BASE = (process.env as any).REACT_APP_API_URL || 'http://localhost:8000/api';
        const token = localStorage.getItem('access_token');
        
        const response = await axios.get(`${API_BASE}/documents/${documentId}/pdf-test`, {
          responseType: 'blob',
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        
        
        // Create blob URL for react-pdf-selection
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const blobUrl = URL.createObjectURL(blob);
        setPdfData(blobUrl);
        
      } catch (err: any) {
        setError('Failed to load PDF document');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPdfData();
    
    // Cleanup blob URL on unmount
    return () => {
      if (pdfData) {
        URL.revokeObjectURL(pdfData);
      }
    };
  }, [url]);

  // Handle text selection from react-pdf-selection
  const handleTextSelection = (selection?: NormalizedTextSelection) => {
    if (onTextSelection && selection) {
      const position = selection.position;
      
      // Convert normalized coordinates to our format, including individual rects
      const coordinates = {
        x: position.normalized.boundingRect.left,
        y: position.normalized.boundingRect.top,
        width: position.normalized.boundingRect.right - position.normalized.boundingRect.left,
        height: position.normalized.boundingRect.bottom - position.normalized.boundingRect.top,
        rects: position.normalized.rects  // Store individual line rectangles
      };
      
      
      onTextSelection({
        text: selection.text,
        pageNumber: position.pageNumber,
        coordinates
      });
    }
  };

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3.0));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (isLoading || !pdfData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>Loading PDF...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* PDF Controls */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 2, 
        p: 1, 
        borderBottom: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper'
      }}>
        <IconButton onClick={handleZoomOut} size="small">
          <ZoomOut />
        </IconButton>
        <Typography variant="body2">
          {Math.round(scale * 100)}%
        </Typography>
        <IconButton onClick={handleZoomIn} size="small">
          <ZoomIn />
        </IconButton>
      </Box>

      {/* PDF Content using react-pdf-selection */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <PdfViewer
          url={pdfData}
          scale={scale}
          overscanCount={0}
          selections={selectionAnnotations}
          onTextSelection={handleTextSelection}
          textSelectionColor="rgba(33, 150, 243, 0.4)"
          textSelectionComponent={({ textSelection }: { textSelection: TextSelectionWithCSSProperties<any> }) => {
            return (
            <div>
              {textSelection.position.rects.map((rect: any, i: number) => {
                
                return (
                <div
                  key={i}
                  className="pdf-highlight-enhanced"
                  style={{
                    ...rect,
                    cursor: 'pointer',
                    position: 'absolute',
                    background: 'rgba(255, 235, 59, 0.2)',
                    border: '1px solid #FF6F00',
                    zIndex: 999
                  }}
                  onClick={() => onAnnotationClick?.(textSelection)}
                  title={`${(textSelection as any).author}: ${(textSelection as any).comment}`}
                />
              );
              })}
            </div>
            );
          }}
        />
      </Box>
    </Box>
  );
};

export default PDFViewer;