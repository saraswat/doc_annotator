export interface Annotation {
  id: string;
  documentId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  createdAt: Date;
  updatedAt?: Date;
  
  // Position in document
  target: AnnotationTarget;
  
  // Annotation content
  body: AnnotationBody;
  
  // Threading and status
  replies?: Annotation[];
  replyTo?: string;
  resolved: boolean;
  resolvedBy?: string;
  resolvedAt?: Date;
  
  // For PDF documents
  pageNumber?: number;
  
  // Permissions
  canEdit: boolean;
  canDelete: boolean;
}

export interface AnnotationTarget {
  selector: TextSelector | XPathSelector;
  source?: string;  // Document URL or ID
}

export interface TextSelector {
  type: 'TextQuoteSelector' | 'TextPositionSelector';
  exact: string;      // The exact quoted text
  prefix?: string;    // Text before the quote
  suffix?: string;    // Text after the quote
  start?: number;     // Start position
  end?: number;       // End position
}

export interface XPathSelector {
  type: 'XPathSelector';
  xpath: string;
  offset?: number;
}

export interface AnnotationBody {
  type: 'TextualBody' | 'Highlight' | 'Tag';
  value: string;
  purpose: 'commenting' | 'highlighting' | 'tagging' | 'questioning';
  color?: string;  // For highlights
  tags?: string[]; // For categorization
}

export interface CreateAnnotationDto {
  documentId: string;
  target: AnnotationTarget;
  body: AnnotationBody;
  replyTo?: string;
}