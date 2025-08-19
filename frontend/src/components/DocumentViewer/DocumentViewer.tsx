import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Container,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { ArrowBack, Comment, Cancel, Save, Description, Delete } from '@mui/icons-material';
import apiService from '../../services/api';
import { useAnnotation } from '../../contexts/AnnotationContext';
import { useAuth } from '../../contexts/AuthContext';
import PDFViewer from '../PDF/PDFViewer';

// Add global styles for annotation highlighting
const annotationStyles = `
  .annotation-highlight {
    background-color: rgba(255, 235, 59, 0.3) !important;
    border-bottom: 2px solid #FFC107 !important;
    cursor: pointer !important;
    transition: background-color 0.2s ease !important;
  }
  
  .annotation-highlight:hover {
    background-color: rgba(255, 235, 59, 0.5) !important;
    border-bottom-color: #FF9800 !important;
  }
  
  .highlight-flash {
    animation: highlightFlash 2s ease-in-out !important;
  }
  
  @keyframes highlightFlash {
    0% { background-color: rgba(33, 150, 243, 0.2); }
    50% { background-color: rgba(33, 150, 243, 0.4); }
    100% { background-color: transparent; }
  }
`;

// Inject styles on component mount
const injectStyles = () => {
  if (typeof window !== 'undefined' && !window.document.getElementById('annotation-styles')) {
    const styleSheet = window.document.createElement('style');
    styleSheet.id = 'annotation-styles';
    styleSheet.innerHTML = annotationStyles;
    window.document.head.appendChild(styleSheet);
  }
};

interface Document {
  id: number;
  title: string;
  document_type: string;
  content: string;
  description?: string;
  filename: string;
}

const DocumentViewer: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [document, setDocument] = useState<Document | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [commentText, setCommentText] = useState('');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  
  const { 
    annotations, 
    currentSelection, 
    isCreatingAnnotation,
    isLoading: annotationsLoading,
    setCurrentSelection, 
    createAnnotation, 
    loadAnnotations,
    cancelAnnotation,
    deleteAnnotation
  } = useAnnotation();

  // Inject CSS styles on mount
  useEffect(() => {
    injectStyles();
  }, []);

  useEffect(() => {
    let isMounted = true;
    
    const fetchDocument = async () => {
      if (!documentId) {
        if (isMounted) {
          setError('Document ID not provided');
          setIsLoading(false);
        }
        return;
      }

      try {
        if (isMounted) {
          setIsLoading(true);
          setError(null);
        }

        // Fetch document details
        const response = await apiService.get(`/documents/${documentId}/`);
        
        if (isMounted) {
          setDocument(response.data);
          
          // If it's a PDF, set the direct PDF URL  
          if (response.data.document_type?.toLowerCase() === 'pdf') {
            const pdfUrl = `/documents/${documentId}/pdf-test`;
            setPdfUrl(pdfUrl);
          }
        }
        
        // Load existing annotations for this document
        if (isMounted) {
          await loadAnnotations(parseInt(documentId));
        }
        
      } catch (error) {
        console.error('Error fetching document:', error);
        if (isMounted) {
          setError('Failed to load document. Please try again.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchDocument();
    
    return () => {
      isMounted = false;
    };
  }, [documentId, loadAnnotations]);


  // Handle text selection with proper character offset calculation
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) {
        return;
      }

      const selectedText = selection.toString().trim();
      if (selectedText.length === 0) {
        return;
      }

      const range = selection.getRangeAt(0);
      
      // Calculate proper character offsets relative to document content
      const documentContainer = window.document.querySelector('.document-content');
      if (!documentContainer) {
        console.warn('Document container not found for selection');
        return;
      }

      // Calculate start and end offsets relative to the document container
      const startOffset = getCharacterOffset(documentContainer, range.startContainer, range.startOffset);
      const endOffset = getCharacterOffset(documentContainer, range.endContainer, range.endOffset);

      // Temporarily highlight the selected text with a different color while creating annotation
      const tempHighlight = window.document.createElement('span');
      tempHighlight.style.backgroundColor = 'rgba(33, 150, 243, 0.3)';
      tempHighlight.style.border = '1px dashed #2196F3';
      tempHighlight.className = 'temp-selection-highlight';
      
      try {
        range.surroundContents(tempHighlight);
      } catch (e) {
        // If surrounding fails, just proceed without temp highlight
        console.warn('Failed to surround selection with temp highlight:', e);
      }

      setCurrentSelection({
        text: selectedText,
        startOffset,
        endOffset,
        range
      });
    };

    // Helper function to calculate character offset from container start
    const getCharacterOffset = (container: Element, node: Node, offset: number): number => {
      const walker = window.document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT
      );

      let totalOffset = 0;
      let currentNode;
      
      while (currentNode = walker.nextNode()) {
        if (currentNode === node) {
          return totalOffset + offset;
        }
        totalOffset += (currentNode.textContent || '').length;
      }
      
      return totalOffset;
    };

    window.document.addEventListener('mouseup', handleSelection);
    window.document.addEventListener('keyup', handleSelection);

    return () => {
      window.document.removeEventListener('mouseup', handleSelection);
      window.document.removeEventListener('keyup', handleSelection);
    };
  }, [setCurrentSelection]);

  // DOM-based highlighting function using character offsets
  const applyDOMHighlighting = useMemo(() => {
    return () => {
      // Get the document content container
      const documentContainer = window.document.querySelector('.document-content');
      if (!documentContainer) {
        return;
      }

      // Always remove existing highlights first
      const existingHighlights = documentContainer.querySelectorAll('.annotation-highlight');
      existingHighlights.forEach(highlight => {
        const parent = highlight.parentNode;
        if (parent) {
          parent.replaceChild(window.document.createTextNode(highlight.textContent || ''), highlight);
          parent.normalize();
        }
      });

      // If no annotations, just return after cleanup
      if (!annotations || annotations.length === 0) {
        return;
      }

      // Filter valid annotations with character offsets
      const validAnnotations = annotations.filter(ann => 
        ann.text && 
        ann.text !== "Document-level comment" && 
        ann.text.length > 0 &&
        typeof ann.startOffset === 'number' &&
        typeof ann.endOffset === 'number' &&
        ann.endOffset > ann.startOffset
      ).sort((a, b) => a.startOffset - b.startOffset); // Sort by start offset

      if (validAnnotations.length === 0) {
        return;
      }

      // Get document text and safety check
      const fullText = documentContainer.textContent || '';
      
      // Safety check: if document looks too short, don't manipulate it
      if (fullText.length < 100) {
        return;
      }

      // Get all text nodes in the document
      const walker = window.document.createTreeWalker(
        documentContainer,
        NodeFilter.SHOW_TEXT
      );

      const textNodes: Text[] = [];
      let node;
      while (node = walker.nextNode()) {
        textNodes.push(node as Text);
      }

      // Build character offset map for text nodes
      let totalOffset = 0;
      const nodeOffsets: Array<{ node: Text; start: number; end: number }> = [];
      
      textNodes.forEach(textNode => {
        const nodeText = textNode.textContent || '';
        nodeOffsets.push({
          node: textNode,
          start: totalOffset,
          end: totalOffset + nodeText.length
        });
        totalOffset += nodeText.length;
      });

      // Total document processed

      // Apply highlights in reverse order to avoid offset shifts
      validAnnotations.reverse().forEach(annotation => {
        try {
          // Find the text nodes that contain this annotation
          const startNodeInfo = nodeOffsets.find(n => 
            annotation.startOffset >= n.start && annotation.startOffset < n.end
          );
          const endNodeInfo = nodeOffsets.find(n => 
            annotation.endOffset > n.start && annotation.endOffset <= n.end
          );

          if (!startNodeInfo || !endNodeInfo) {
            return;
          }

          const range = window.document.createRange();
          
          // Set the start position
          const startOffsetInNode = annotation.startOffset - startNodeInfo.start;
          range.setStart(startNodeInfo.node, Math.max(0, Math.min(startOffsetInNode, startNodeInfo.node.textContent?.length || 0)));
          
          // Set the end position
          const endOffsetInNode = annotation.endOffset - endNodeInfo.start;
          range.setEnd(endNodeInfo.node, Math.max(0, Math.min(endOffsetInNode, endNodeInfo.node.textContent?.length || 0)));

          // Verify the range text matches the annotation text
          const rangeText = range.toString();
          const expectedText = fullText.substring(annotation.startOffset, annotation.endOffset);
          
          if (rangeText !== annotation.text) {
            // Try to find the correct text in the document
            const textIndex = fullText.indexOf(annotation.text);
            if (textIndex !== -1) {
              // Use the found position
              const correctedStartNode = nodeOffsets.find(n => textIndex >= n.start && textIndex < n.end);
              const correctedEndNode = nodeOffsets.find(n => (textIndex + annotation.text.length) > n.start && (textIndex + annotation.text.length) <= n.end);
              
              if (correctedStartNode && correctedEndNode) {
                range.setStart(correctedStartNode.node, textIndex - correctedStartNode.start);
                range.setEnd(correctedEndNode.node, (textIndex + annotation.text.length) - correctedEndNode.start);
              }
            }
          }

          // Create highlight span
          const highlightSpan = window.document.createElement('span');
          highlightSpan.className = 'annotation-highlight';
          highlightSpan.setAttribute('data-annotation-id', annotation.id);
          highlightSpan.setAttribute('title', annotation.comment);
          highlightSpan.style.cssText = 'background: rgba(255, 235, 59, 0.4) !important; border-bottom: 2px solid #FFC107 !important; cursor: pointer !important;';

          // Wrap the range content - be more careful to preserve document structure
          try {
            // Check if the range spans multiple elements or nodes
            if (range.startContainer === range.endContainer && range.startContainer.nodeType === Node.TEXT_NODE) {
              // Simple case: selection is within a single text node
              range.surroundContents(highlightSpan);
            } else {
              // Complex case: selection spans multiple nodes, use clone and insert approach
              const clonedRange = range.cloneRange();
              const contents = clonedRange.extractContents();
              highlightSpan.appendChild(contents);
              range.insertNode(highlightSpan);
            }
          } catch (e) {
            // Skip highlighting if DOM manipulation fails
          }
        } catch (error) {
          // Skip annotation if processing fails
        }
      });
    };
  }, [annotations]);

  // Apply DOM highlighting after content is rendered
  useEffect(() => {
    if (document?.content && annotations) {
      // Small delay to ensure DOM is fully rendered
      const timer = setTimeout(() => {
        applyDOMHighlighting();
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [document?.content, annotations, applyDOMHighlighting]);

  // Handle clicking on annotation highlights
  useEffect(() => {
    const handleAnnotationClick = (event: Event) => {
      const target = event.target as HTMLElement;
      if (target.classList.contains('annotation-highlight')) {
        const annotationId = target.getAttribute('data-annotation-id');
        if (annotationId) {
          // Scroll to the annotation in the sidebar
          const annotationElement = window.document.querySelector(`[data-annotation-card-id="${annotationId}"]`);
          if (annotationElement) {
            annotationElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Add temporary highlight effect
            annotationElement.classList.add('highlight-flash');
            setTimeout(() => annotationElement.classList.remove('highlight-flash'), 2000);
          }
        }
      }
    };

    window.document.addEventListener('click', handleAnnotationClick);
    return () => window.document.removeEventListener('click', handleAnnotationClick);
  }, []);

  const handleCreateAnnotation = async () => {
    if (commentText.trim() && documentId) {
      // Remove temporary highlight before creating annotation
      const tempHighlights = window.document.querySelectorAll('.temp-selection-highlight');
      tempHighlights.forEach(el => {
        const parent = el.parentNode;
        if (parent) {
          parent.replaceChild(window.document.createTextNode(el.textContent || ''), el);
          parent.normalize();
        }
      });
      
      await createAnnotation(commentText.trim(), parseInt(documentId));
      setCommentText('');
    }
  };

  const handleCancelAnnotation = () => {
    // Remove temporary highlight
    const tempHighlights = window.document.querySelectorAll('.temp-selection-highlight');
    tempHighlights.forEach(el => {
      const parent = el.parentNode;
      if (parent) {
        parent.replaceChild(window.document.createTextNode(el.textContent || ''), el);
        parent.normalize();
      }
    });
    
    cancelAnnotation();
    setCommentText('');
  };

  // Handle PDF text selection
  const handlePDFTextSelection = (selection: {
    text: string;
    pageNumber: number;
    coordinates: { x: number; y: number; width: number; height: number };
  }) => {
    
    // For PDFs, we'll store the page number and coordinates instead of character offsets
    setCurrentSelection({
      text: selection.text,
      startOffset: 0, // Not applicable for PDFs
      endOffset: 0,   // Not applicable for PDFs
      range: null as any,
      pageNumber: selection.pageNumber,
      coordinates: selection.coordinates
    });
  };

  // Handle clicking on PDF annotations
  const handlePDFAnnotationClick = (annotation: any) => {
    // Scroll to the annotation in the sidebar
    const annotationElement = window.document.querySelector(`[data-annotation-card-id="${annotation.id}"]`);
    if (annotationElement) {
      annotationElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Add temporary highlight effect
      annotationElement.classList.add('highlight-flash');
      setTimeout(() => annotationElement.classList.remove('highlight-flash'), 2000);
    }
  };

  // Handle clicking on annotation card to scroll to page/text
  const handleAnnotationCardClick = (annotation: any) => {
    // For PDF documents - scroll to page
    const pageNum = (annotation as any).position?.pageNumber || (annotation as any).target?.selector?.pageNumber || annotation.pageNumber;
    
    if (pageNum && pdfUrl) {
      
      // Try multiple selectors to find the PDF page
      const selectors = [
        `[data-page-number="${annotation.pageNumber}"]`,
        `.react-pdf__Page[data-page-number="${annotation.pageNumber}"]`,
        `.react-pdf__Page:nth-child(${annotation.pageNumber})`,
        `[data-testid="page-${annotation.pageNumber}"]`,
        `.page-${annotation.pageNumber}`
      ];
      
      let pageElement = null;
      for (const selector of selectors) {
        pageElement = window.document.querySelector(selector);
        if (pageElement) {
          break;
        }
      }
      
      if (pageElement) {
        pageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        // Fallback: scroll to page by index
        const pageContainers = Array.from(window.document.querySelectorAll('.pdfViewer__page-container'));
        if (pageContainers.length >= pageNum) {
          const targetPage = pageContainers[pageNum - 1];
          targetPage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    } else if (!pdfUrl) {
      // For HTML/Markdown documents - scroll to highlighted text
      const highlightElement = window.document.querySelector(`[data-annotation-id="${annotation.id}"]`);
      if (highlightElement) {
        highlightElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Add temporary flash effect
        highlightElement.classList.add('highlight-flash');
        setTimeout(() => highlightElement.classList.remove('highlight-flash'), 2000);
      }
    }
  };


  if (isLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%' 
      }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!document) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning">Document not found</Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', position: 'relative' }}>
      {/* Document content */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, paddingRight: '320px' }}>
        <Container maxWidth="lg" sx={{ py: 2, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, flexShrink: 0 }}>
            <Typography variant="h4" gutterBottom>
              {document.title}
            </Typography>
          </Box>
          
          <Paper 
            elevation={1} 
            sx={{ p: 3, bgcolor: 'white', flex: 1, overflow: 'auto', minHeight: 0 }}
            className="document-content"
          >
            {document.document_type?.toLowerCase() === 'pdf' ? (
              pdfUrl ? (
                <PDFViewer 
                  url={pdfUrl}
                  annotations={annotations}
                  onTextSelection={handlePDFTextSelection}
                  onAnnotationClick={handlePDFAnnotationClick}
                />
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                  <CircularProgress />
                  <Typography variant="body2" sx={{ ml: 2 }}>Loading PDF...</Typography>
                </Box>
              )
            ) : (
              <div 
                dangerouslySetInnerHTML={{ __html: document.content }}
                style={{ 
                  userSelect: 'text',
                  lineHeight: 1.6,
                  whiteSpace: document.document_type === 'MARKDOWN' ? 'pre-wrap' : 'normal',
                  fontFamily: document.document_type === 'MARKDOWN' ? 'inherit' : 'inherit'
                }}
              />
            )}
          </Paper>
        </Container>
      </Box>
      
      {/* Annotation sidebar - Fixed to viewport */}
      <Box sx={{ 
        position: 'fixed',
        top: 64, // Account for header height
        right: 0,
        width: 320, 
        height: 'calc(100vh - 64px)', // Full height minus header
        borderLeft: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        overflow: 'auto',
        zIndex: 1000
      }}>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Annotations
          </Typography>
          
          {/* Add document-level annotation button */}
          <Box sx={{ mb: 2 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Comment />}
              onClick={() => setCurrentSelection({ text: '', startOffset: 0, endOffset: 0, range: null as any })}
              disabled={isCreatingAnnotation}
            >
              Add Document Comment
            </Button>
          </Box>

          {/* Show annotation creation form when text is selected OR document comment is being created */}
          {isCreatingAnnotation && (
            <Card sx={{ mb: 2, border: '2px solid', borderColor: 'primary.main' }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom color="primary">
                  {currentSelection?.text ? 'Creating annotation for:' : 'Creating document comment:'}
                </Typography>
                {currentSelection?.text && (
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      mb: 2, 
                      p: 1, 
                      bgcolor: 'grey.100', 
                      borderRadius: 1,
                      fontStyle: 'italic'
                    }}
                  >
                    "{currentSelection.text}"
                  </Typography>
                )}
                {!currentSelection?.text && (
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      mb: 2, 
                      p: 1, 
                      bgcolor: 'grey.100', 
                      borderRadius: 1,
                      fontStyle: 'italic'
                    }}
                  >
                    General comment on document
                  </Typography>
                )}
                
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder={currentSelection?.text ? "Add your comment..." : "Add a general comment about this document..."}
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  sx={{ mb: 2 }}
                />
                
                <Stack direction="row" spacing={1}>
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<Save />}
                    onClick={handleCreateAnnotation}
                    disabled={!commentText.trim() || annotationsLoading}
                  >
                    {annotationsLoading ? 'Saving...' : 'Save'}
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Cancel />}
                    onClick={handleCancelAnnotation}
                  >
                    Cancel
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          )}
          
          {/* Show existing annotations */}
          {annotationsLoading && annotations.length === 0 ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress size={20} />
            </Box>
          ) : annotations.length > 0 ? (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                {annotations.length} annotation{annotations.length !== 1 ? 's' : ''}
              </Typography>
              
              {annotations.map((annotation) => (
                <Card 
                  key={annotation.id} 
                  sx={{ 
                    mb: 2, 
                    cursor: annotation.pageNumber ? 'pointer' : 'default',
                    '&:hover': annotation.pageNumber ? {
                      bgcolor: 'action.hover'
                    } : {}
                  }} 
                  data-annotation-card-id={annotation.id}
                  onClick={() => handleAnnotationCardClick(annotation)}
                >
                  <CardContent>
                    {annotation.text && annotation.text !== "Document-level comment" && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        "{annotation.text}"
                      </Typography>
                    )}
                    {(!annotation.text || annotation.text === "Document-level comment") && (
                      <Typography variant="body2" color="primary.main" gutterBottom sx={{ fontWeight: 'medium' }}>
                        📄 Document Comment
                      </Typography>
                    )}
                    
                    <Typography variant="body1" sx={{ mb: 1 }}>
                      {annotation.comment}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip 
                          label={annotation.author}
                          size="small"
                          variant="outlined"
                        />
                        <Chip 
                          label={`Page ${annotation.pageNumber || 1}`}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {new Date(annotation.createdAt).toLocaleDateString()}
                        </Typography>
                      </Box>
                      <Box onClick={(e) => e.stopPropagation()}>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation(); // Prevent card click
                            deleteAnnotation(annotation.id);
                          }}
                          disabled={annotationsLoading}
                          sx={{ color: 'error.main' }}
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          ) : !isCreatingAnnotation && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Select text in the document to create annotations.
            </Alert>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default DocumentViewer;