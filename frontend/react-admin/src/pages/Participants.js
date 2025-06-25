import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Avatar from '@mui/material/Avatar';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PhotoIcon from '@mui/icons-material/Photo';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import { getProjectParticipants, getAllParticipants, createParticipant, addParticipantToProject, removeParticipantFromProject, uploadAvatar } from '../services/api';

function Participants() {
  const { projectId } = useParams(); // This is a string
  const [participants, setParticipants] = useState([]);
  const [allParticipants, setAllParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [participantToDelete, setParticipantToDelete] = useState(null);
  const [newParticipantName, setNewParticipantName] = useState('');
  const [avatarFile, setAvatarFile] = useState(null); // This will hold the File object
  const [selectedExistingParticipant, setSelectedExistingParticipant] = useState('');
  const [addParticipantTab, setAddParticipantTab] = useState(0); // 0 = New, 1 = Existing
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');

  // Fetch project participants
  const fetchProjectParticipants = useCallback(async () => {
    setLoading(true);
    try {
      console.log(`[Participants.js] Fetching participants for project ID: ${projectId}`);
      const response = await getProjectParticipants(projectId);
      setParticipants(Array.isArray(response.data) ? response.data : []);
      console.log('[Participants.js] Fetched participants:', response.data);
    } catch (error) {
      console.error('[Participants.js] Error fetching project participants:', error);
      setSnackbarMessage(`Error fetching participants: ${error.message}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      setParticipants([]);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // Fetch all participants
  const fetchAllParticipants = useCallback(async () => {
    try {
      console.log('[Participants.js] Fetching all participants');
      const response = await getAllParticipants();
      setAllParticipants(Array.isArray(response.data) ? response.data : []);
      console.log('[Participants.js] Fetched all participants:', response.data);
    } catch (error) {
      console.error('[Participants.js] Error fetching all participants:', error);
    }
  }, []);

  useEffect(() => {
    fetchProjectParticipants();
    fetchAllParticipants();
  }, [fetchProjectParticipants, fetchAllParticipants]);

  const handleAddDialogOpen = () => {
    setOpenAddDialog(true);
    setNewParticipantName('');
    setAvatarFile(null);
    setSelectedExistingParticipant('');
    setAddParticipantTab(0); // Default to 'New Participant' tab
  };

  const handleAddDialogClose = () => {
    setOpenAddDialog(false);
    setNewParticipantName('');
    setAvatarFile(null);
    setSelectedExistingParticipant('');
  };
  
  const handleTabChange = (event, newValue) => {
    setAddParticipantTab(newValue);
  };

  const handleDeleteDialogOpen = (participant) => {
    setParticipantToDelete(participant);
    setOpenDeleteDialog(true);
  };

  const handleDeleteDialogClose = () => {
    setOpenDeleteDialog(false);
    setParticipantToDelete(null);
  };

  const handleAddParticipant = async () => {
    if (addParticipantTab === 0) { // Adding a new participant
      if (!newParticipantName.trim()) {
        setSnackbarMessage('Participant name cannot be empty.');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
        return;
      }

      try {
        let uploadedAvatarFilename = null;
        if (avatarFile) {
          const formData = new FormData();
          formData.append('file', avatarFile);
          console.log('[Participants.js] Uploading avatar:', avatarFile.name);
          const avatarUploadResponse = await uploadAvatar(formData);
          uploadedAvatarFilename = avatarUploadResponse.data.filename;
          console.log('[Participants.js] Avatar uploaded, filename:', uploadedAvatarFilename);
        }

        const participantData = {
          name: newParticipantName,
          avatar_filename: uploadedAvatarFilename,
        };

        console.log('[Participants.js] Creating participant with data:', participantData);
        const response = await createParticipant(participantData);
        const createdParticipant = response.data;
        console.log('[Participants.js] Participant created:', createdParticipant);

        // Now associate the newly created participant with the current project
        console.log(`[Participants.js] Associating participant ID: ${createdParticipant.id} with project ID: ${projectId}`);
        await addParticipantToProject(projectId, createdParticipant.id);
        console.log('[Participants.js] Participant associated with project successfully.');

        // Re-fetch participants to update the UI
        fetchProjectParticipants(); 

        setSnackbarMessage('Participant added successfully!');
        setSnackbarSeverity('success');
        setSnackbarOpen(true);
        handleAddDialogClose();
      } catch (error) {
        console.error('[Participants.js] Error adding participant:', error);
        setSnackbarMessage(`Error adding participant: ${error.response?.data?.detail || error.message}`);
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    } else { // Adding an existing participant
      if (!selectedExistingParticipant) {
        setSnackbarMessage('Please select an existing participant.');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
        return;
      }

      try {
        console.log(`[Participants.js] Adding existing participant ID: ${selectedExistingParticipant} to project ID: ${projectId}`);
        await addParticipantToProject(projectId, selectedExistingParticipant);
        console.log('[Participants.js] Existing participant added to project successfully.');

        // Re-fetch participants to update the UI
        fetchProjectParticipants();

        setSnackbarMessage(`Participant added to project successfully!`);
        setSnackbarSeverity('success');
        setSnackbarOpen(true);
        handleAddDialogClose();
      } catch (error) {
        console.error('[Participants.js] Error adding existing participant to project:', error);
        setSnackbarMessage(`Error adding existing participant to project: ${error.response?.data?.detail || error.message}`);
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    }
  };

  const handleDeleteParticipant = async () => {
    if (!participantToDelete) return;

    try {
      console.log(`[Participants.js] Deleting participant ID: ${participantToDelete.id} from project ID: ${projectId}`);
      await removeParticipantFromProject(projectId, participantToDelete.id);
      console.log('[Participants.js] Participant deleted successfully from backend.');

      // Re-fetch participants to update the UI
      fetchProjectParticipants();

      setSnackbarMessage(`Participant "${participantToDelete.name}" deleted successfully`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      handleDeleteDialogClose();
    } catch (error) {
      console.error('[Participants.js] Error deleting participant:', error);
      setSnackbarMessage(`Error deleting participant: ${error.response?.data?.detail || error.message}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  const handleAvatarChange = (event) => {
    if (event.target.files && event.target.files[0]) {
      setAvatarFile(event.target.files[0]);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Participants
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={handleAddDialogOpen}
        >
          Add Participant
        </Button>
      </Box>

      {loading ? (
        <Typography>Loading participants...</Typography>
      ) : participants.length > 0 ? (
        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }} aria-label="participants table">
            <TableHead>
              <TableRow>
                <TableCell>Avatar</TableCell>
                <TableCell>Name</TableCell>
                <TableCell align="center">Responses</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {participants.map((participant) => (
                <TableRow
                  key={participant.id}
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell component="th" scope="row">
                    <Avatar src={`http://localhost:8000${participant.avatar_path}`} alt={participant.name} />
                  </TableCell>
                  <TableCell>{participant.name}</TableCell>
                  <TableCell align="center">{participant.responses_count}</TableCell>
                  <TableCell align="right">
                    <IconButton 
                      aria-label="delete" 
                      onClick={() => handleDeleteDialogOpen(participant)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" gutterBottom>
            No participants found. Add your first participant to get started.
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={handleAddDialogOpen}
            sx={{ mt: 2 }}
          >
            Add Participant
          </Button>
        </Box>
      )}

      {/* Add Participant Dialog */}
      <Dialog open={openAddDialog} onClose={handleAddDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Add Participant</DialogTitle>
        <DialogContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
            <Tabs value={addParticipantTab} onChange={handleTabChange} aria-label="participant tabs">
              <Tab label="New Participant" />
              <Tab label="Existing Participant" />
            </Tabs>
          </Box>
          
          {addParticipantTab === 0 ? (
            // New Participant Tab
            <Box>
              <DialogContentText>
                Enter the name and optionally upload an avatar for the new participant.
              </DialogContentText>
              <TextField
                autoFocus
                margin="dense"
                id="name"
                label="Participant Name"
                type="text"
                fullWidth
                variant="outlined"
                value={newParticipantName}
                onChange={(e) => setNewParticipantName(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<PhotoIcon />}
                >
                  Upload Avatar
                  <input
                    type="file"
                    hidden
                    accept="image/*"
                    onChange={handleAvatarChange}
                  />
                </Button>
                {avatarFile && (
                  <Box sx={{ ml: 2, display: 'flex', alignItems: 'center' }}>
                    <Avatar 
                      src={URL.createObjectURL(avatarFile)} 
                      alt="Preview"
                      sx={{ width: 40, height: 40, mr: 1 }}
                    />
                    <Typography variant="body2">
                      {avatarFile.name}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>
          ) : (
            // Existing Participant Tab
            <Box>
              <DialogContentText>
                Select an existing participant to add to this project.
              </DialogContentText>
              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel id="existing-participant-label">Select Participant</InputLabel>
                <Select
                  labelId="existing-participant-label"
                  id="existing-participant"
                  value={selectedExistingParticipant}
                  label="Select Participant"
                  onChange={(e) => setSelectedExistingParticipant(e.target.value)}
                >
                  {allParticipants
                    .filter(p => !participants.some(existing => existing.name === p.name))
                    .map((participant) => (
                      <MenuItem key={participant.id} value={participant.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar 
                            src={`http://localhost:8000${participant.avatar_path}`} 
                            alt={participant.name}
                            sx={{ width: 24, height: 24, mr: 1 }}
                          />
                          {participant.name}
                        </Box>
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleAddDialogClose}>Cancel</Button>
          <Button 
            onClick={handleAddParticipant} 
            variant="contained" 
            disabled={addParticipantTab === 0 ? !newParticipantName.trim() : !selectedExistingParticipant}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Participant Dialog */}
      <Dialog
        open={openDeleteDialog}
        onClose={handleDeleteDialogClose}
      >
        <DialogTitle>Delete Participant</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the participant "{participantToDelete?.name}"? This will also delete all of their responses.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteDialogClose}>Cancel</Button>
          <Button onClick={handleDeleteParticipant} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default Participants;
