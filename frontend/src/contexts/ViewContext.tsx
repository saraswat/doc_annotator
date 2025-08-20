import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ViewState, ViewContextType } from '../types/context';

const ViewContext = createContext<ViewContextType | undefined>(undefined);

interface ViewProviderProps {
  children: ReactNode;
}

export const ViewProvider: React.FC<ViewProviderProps> = ({ children }) => {
  const [viewState, setViewState] = useState<ViewState>({
    currentView: 'documents'
  });

  const setCurrentView = (view: 'documents' | 'chat') => {
    setViewState(prev => ({ ...prev, currentView: view }));
  };

  const setCurrentDocument = (documentId?: string) => {
    setViewState(prev => ({ 
      ...prev, 
      currentDocumentId: documentId,
      currentView: documentId ? 'documents' : prev.currentView
    }));
  };

  const setCurrentChatSession = (sessionId?: string) => {
    setViewState(prev => ({ 
      ...prev, 
      currentChatSessionId: sessionId,
      currentView: sessionId ? 'chat' : prev.currentView
    }));
  };

  return (
    <ViewContext.Provider value={{
      viewState,
      setCurrentView,
      setCurrentDocument,
      setCurrentChatSession
    }}>
      {children}
    </ViewContext.Provider>
  );
};

export const useViewContext = () => {
  const context = useContext(ViewContext);
  if (context === undefined) {
    throw new Error('useViewContext must be used within a ViewProvider');
  }
  return context;
};