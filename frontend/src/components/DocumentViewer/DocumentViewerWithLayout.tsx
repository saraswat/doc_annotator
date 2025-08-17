import React from 'react';
import { useParams } from 'react-router-dom';
import MainLayout from '../Layout/MainLayout';
import DocumentViewer from './DocumentViewer';

const DocumentViewerWithLayout: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();

  return (
    <MainLayout currentDocumentId={documentId}>
      <DocumentViewer />
    </MainLayout>
  );
};

export default DocumentViewerWithLayout;