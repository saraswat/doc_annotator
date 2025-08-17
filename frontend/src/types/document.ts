export interface Document {
  id: string;
  title: string;
  filename: string;
  filePath: string;
  fileSize: number;
  type: DocumentType;
  content?: string;
  contentHash?: string;
  description?: string;
  tags?: string;
  ownerId: string;
  isPublic: boolean;
  allowComments: boolean;
  isActive: boolean;
  processingStatus: string;
  createdAt: Date;
  updatedAt: Date;
}

export enum DocumentType {
  HTML = 'html',
  MARKDOWN = 'markdown',
  PDF = 'pdf',
  TEXT = 'text'
}

export interface DocumentListItem {
  id: string;
  title: string;
  description?: string;
  type: DocumentType;
  fileSize: number;
  ownerId: string;
  isPublic: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface DocumentUpload {
  title: string;
  description?: string;
  tags?: string;
  isPublic: boolean;
  allowComments: boolean;
  file: File;
}