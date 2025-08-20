import React from 'react';
import { ToggleButton, ToggleButtonGroup, Box } from '@mui/material';
import { Description as DocumentsIcon, Chat as ChatIcon } from '@mui/icons-material';
import { useViewContext } from '../../contexts/ViewContext';

const ViewToggle: React.FC = () => {
  const { viewState, setCurrentView } = useViewContext();

  const handleViewChange = (
    event: React.MouseEvent<HTMLElement>,
    newView: 'documents' | 'chat' | null
  ) => {
    if (newView !== null) {
      setCurrentView(newView);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
      <ToggleButtonGroup
        value={viewState.currentView}
        exclusive
        onChange={handleViewChange}
        aria-label="view toggle"
        size="small"
      >
        <ToggleButton value="documents" aria-label="documents">
          <DocumentsIcon sx={{ mr: 1 }} />
          Documents
        </ToggleButton>
        <ToggleButton value="chat" aria-label="chat">
          <ChatIcon sx={{ mr: 1 }} />
          Chat
        </ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
};

export default ViewToggle;