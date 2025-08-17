import React, { useRef } from 'react';
import MainLayout from '../Layout/MainLayout';
import DocumentList from './DocumentList';

const DocumentListWithLayout: React.FC = () => {
  const documentListRef = useRef<{ refreshDocuments: () => void }>(null);

  const handleUploadComplete = () => {
    documentListRef.current?.refreshDocuments();
  };

  return (
    <MainLayout onUploadComplete={handleUploadComplete}>
      <DocumentList ref={documentListRef} />
    </MainLayout>
  );
};

export default DocumentListWithLayout;