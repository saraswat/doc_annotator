import React, { createContext, useContext, ReactNode, useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';

interface BackendAnnotation {
  id: string;
  target: {
    selector: {
      type: string;
      startOffset: number;
      endOffset: number;
      selectedText: string;
    };
  };
  body: {
    type: string;
    value: string;
    purpose: string;
  };
  user_name: string;
  created_at: string;
  document_id: number;
}

interface Annotation {
  id: string;
  text: string;
  comment: string;
  startOffset: number;
  endOffset: number;
  createdAt: string;
  author: string;
  // PDF-specific fields
  pageNumber?: number;
  coordinates?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

interface TextSelection {
  text: string;
  startOffset: number;
  endOffset: number;
  range: Range;
  // PDF-specific fields
  pageNumber?: number;
  coordinates?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

interface AnnotationContextType {
  annotations: Annotation[];
  currentSelection: TextSelection | null;
  isCreatingAnnotation: boolean;
  isLoading: boolean;
  setCurrentSelection: (selection: TextSelection | null) => void;
  createAnnotation: (comment: string, documentId: number) => Promise<void>;
  loadAnnotations: (documentId: number) => Promise<void>;
  cancelAnnotation: () => void;
  deleteAnnotation: (annotationId: string) => Promise<void>;
}

const AnnotationContext = createContext<AnnotationContextType | undefined>(undefined);

export const useAnnotation = () => {
  const context = useContext(AnnotationContext);
  if (context === undefined) {
    throw new Error('useAnnotation must be used within an AnnotationProvider');
  }
  return context;
};

interface AnnotationProviderProps {
  children: ReactNode;
}

export const AnnotationProvider: React.FC<AnnotationProviderProps> = ({ children }) => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [currentSelection, setCurrentSelection] = useState<TextSelection | null>(null);
  const [isCreatingAnnotation, setIsCreatingAnnotation] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const transformBackendAnnotation = (backendAnnotation: any): Annotation => {
    // The backend returns target and body as JSON objects directly
    const target = backendAnnotation.target || {};
    const body = backendAnnotation.body || {};
    const selector = target.selector || {};
    
    return {
      id: backendAnnotation.id,
      text: selector.selectedText || '',
      comment: body.value || '',
      startOffset: Number(selector.startOffset) || 0,
      endOffset: Number(selector.endOffset) || 0,
      createdAt: backendAnnotation.created_at,
      author: backendAnnotation.user_name,
      // PDF-specific fields
      pageNumber: selector.pageNumber,
      coordinates: selector.coordinates
    };
  };

  const loadAnnotations = useCallback(async (documentId: number) => {
    try {
      setIsLoading(true);
      // Clear existing annotations first to avoid stale data
      setAnnotations([]);
      
      const response = await apiService.get(`/annotations/document/${documentId}`);
      const backendAnnotations: BackendAnnotation[] = response.data;
      const transformedAnnotations = backendAnnotations.map(transformBackendAnnotation);
      setAnnotations(transformedAnnotations);
    } catch (error) {
      console.error('Error loading annotations:', error);
      setAnnotations([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createAnnotation = async (comment: string, documentId: number) => {
    if (!currentSelection) return;

    try {
      setIsLoading(true);
      
      const annotationData = {
        document_id: documentId,
        target: {
          selector: {
            type: currentSelection.text ? "TextPositionSelector" : "DocumentSelector",
            startOffset: currentSelection.startOffset,
            endOffset: currentSelection.endOffset,
            selectedText: currentSelection.text || "Document-level comment",
            // PDF-specific fields
            pageNumber: currentSelection.pageNumber,
            coordinates: currentSelection.coordinates
          }
        },
        body: {
          type: "TextualBody",
          value: comment,
          purpose: currentSelection.text ? "commenting" : "document_commenting"
        }
      };

      const response = await apiService.post('/annotations/', annotationData);
      const newBackendAnnotation: BackendAnnotation = response.data;
      const newAnnotation = transformBackendAnnotation(newBackendAnnotation);
      
      setAnnotations((prev: Annotation[]) => [...prev, newAnnotation]);
      setCurrentSelection(null);
      setIsCreatingAnnotation(false);

      // Clear the browser selection
      window.getSelection()?.removeAllRanges();
    } catch (error) {
      console.error('Error creating annotation:', error);
      // Keep the creation form open on error
    } finally {
      setIsLoading(false);
    }
  };

  const cancelAnnotation = () => {
    setCurrentSelection(null);
    setIsCreatingAnnotation(false);
    window.getSelection()?.removeAllRanges();
  };

  const deleteAnnotation = async (annotationId: string) => {
    try {
      setIsLoading(true);
      await apiService.delete(`/annotations/${annotationId}`);
      
      // Remove annotation from local state
      setAnnotations(prev => prev.filter(ann => ann.id !== annotationId));
    } catch (error) {
      console.error('Error deleting annotation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetCurrentSelection = (selection: TextSelection | null) => {
    setCurrentSelection(selection);
    setIsCreatingAnnotation(!!selection);
  };

  const value: AnnotationContextType = {
    annotations,
    currentSelection,
    isCreatingAnnotation,
    isLoading,
    setCurrentSelection: handleSetCurrentSelection,
    createAnnotation,
    loadAnnotations,
    cancelAnnotation,
    deleteAnnotation
  };

  return (
    <AnnotationContext.Provider value={value}>
      {children}
    </AnnotationContext.Provider>
  );
};