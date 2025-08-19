import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Typography,
  Chip,
  Alert
} from '@mui/material';
import { Delete, PersonAdd, Lock } from '@mui/icons-material';
import api from '../../services/api';
import { User } from '../../types/user';

interface CreateUserData {
  email: string;
  name: string;
  password: string;
  is_admin: boolean;
}

interface ResetPasswordData {
  new_password: string;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [createUserData, setCreateUserData] = useState<CreateUserData>({
    email: '',
    name: '',
    password: '',
    is_admin: false
  });
  
  const [resetPasswordData, setResetPasswordData] = useState<ResetPasswordData>({
    new_password: ''
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/users/');
      setUsers(response.data);
    } catch (error) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    try {
      await api.post('/admin/users/', createUserData);
      setSuccess('User created successfully');
      setCreateDialogOpen(false);
      setCreateUserData({ email: '', name: '', password: '', is_admin: false });
      loadUsers();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await api.delete(`/admin/users/${userId}/`);
        setSuccess('User deleted successfully');
        loadUsers();
      } catch (error: any) {
        setError(error.response?.data?.detail || 'Failed to delete user');
      }
    }
  };

  const handleResetPassword = async () => {
    if (!selectedUserId) return;
    
    try {
      await api.post(`/admin/users/${selectedUserId}/reset-password/`, {
        email: '', // Not needed for admin reset
        new_password: resetPasswordData.new_password
      });
      setSuccess('Password reset successfully');
      setResetPasswordDialogOpen(false);
      setResetPasswordData({ new_password: '' });
      setSelectedUserId(null);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  const openResetPasswordDialog = (userId: number) => {
    setSelectedUserId(userId);
    setResetPasswordDialogOpen(true);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">User Management</Typography>
        <Button
          variant="contained"
          startIcon={<PersonAdd />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create User
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Email</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Auth Type</TableCell>
              <TableCell>Admin</TableCell>
              <TableCell>Active</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.email}</TableCell>
                <TableCell>{user.name}</TableCell>
                <TableCell>
                  <Chip
                    label={user.oauthProvider || 'Password'}
                    color={user.oauthProvider ? 'primary' : 'secondary'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.isAdmin ? 'Admin' : 'User'}
                    color={user.isAdmin ? 'error' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.isActive ? 'Active' : 'Inactive'}
                    color={user.isActive ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {new Date(user.createdAt).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <IconButton
                    color="primary"
                    onClick={() => openResetPasswordDialog(user.id)}
                    disabled={!!user.oauthProvider}
                    title="Reset Password"
                  >
                    <Lock />
                  </IconButton>
                  <IconButton
                    color="error"
                    onClick={() => handleDeleteUser(user.id)}
                    title="Delete User"
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New User</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            variant="outlined"
            value={createUserData.email}
            onChange={(e) => setCreateUserData({ ...createUserData, email: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Name"
            fullWidth
            variant="outlined"
            value={createUserData.name}
            onChange={(e) => setCreateUserData({ ...createUserData, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Initial Password"
            type="password"
            fullWidth
            variant="outlined"
            value={createUserData.password}
            onChange={(e) => setCreateUserData({ ...createUserData, password: e.target.value })}
            helperText="User will be required to change this password on first login"
          />
          <FormControlLabel
            control={
              <Switch
                checked={createUserData.is_admin}
                onChange={(e) => setCreateUserData({ ...createUserData, is_admin: e.target.checked })}
              />
            }
            label="Admin User"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateUser} variant="contained">Create User</Button>
        </DialogActions>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={resetPasswordDialogOpen} onClose={() => setResetPasswordDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Reset User Password</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="New Password"
            type="password"
            fullWidth
            variant="outlined"
            value={resetPasswordData.new_password}
            onChange={(e) => setResetPasswordData({ new_password: e.target.value })}
            helperText="User will be required to change this password on next login"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetPasswordDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleResetPassword} variant="contained">Reset Password</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;