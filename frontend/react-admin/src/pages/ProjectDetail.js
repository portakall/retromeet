import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import CircularProgress from '@mui/material/CircularProgress';
import PeopleIcon from '@mui/icons-material/People';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import SummarizeIcon from '@mui/icons-material/Summarize';
import LinkIcon from '@mui/icons-material/Link';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { 
  getProject, 
  getProjectParticipants, 
  getAllParticipants,
  addParticipantToProject,
  removeParticipantFromProject,
  createParticipant,
  generateChatLink, 
  getChatLink, 
  generateSummary, 
  getSummary 
} from '../services/api';

function ProjectDetail({ setCurrentProject }) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chatLink, setChatLink] = useState('');
  const [openLinkDialog, setOpenLinkDialog] = useState(false);
  const [summary, setSummary] = useState('');
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');

  const loadProject = useCallback(async () => {
    setLoading(true);
    try {
      console.log(`[ProjectDetail.js] Loading project ID: ${projectId}`);
      const projectResponse = await getProject(projectId);
      console.log('[ProjectDetail.js] Project loaded:', projectResponse.data);
      setProject(projectResponse.data);
      setCurrentProject(projectResponse.data);
      
      // Fetch actual participants
      await fetchProjectParticipants();
      
      setLoading(false);
    } catch (error) {
      console.error('[ProjectDetail.js] Error loading project:', error);
      setSnackbarMessage('Error loading project');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      setLoading(false);
    }
  }, [projectId, setCurrentProject]);

  const fetchProjectParticipants = useCallback(async () => {
    try {
      console.log(`[ProjectDetail.js] Fetching participants for project ID: ${projectId}`);
      const response = await getProjectParticipants(projectId);
      console.log('[ProjectDetail.js] Project participants fetched successfully:', response.data);
      setParticipants(response.data);
    } catch (error) {
      console.error('[ProjectDetail.js] Error fetching project participants:', error);
      setSnackbarMessage('Failed to load project participants');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      loadProject();
    }
  }, [projectId, loadProject]);

  const handleGenerateChatLink = async () => {
    try {
      console.log('[ProjectDetail.js] Generating chat link for participants:', participants);
      const participantsForChat = participants.map(p => ({
        id: p.id,
        name: p.name,
        avatar_path: p.avatar_path
      }));
      
      const response = await generateChatLink(projectId, participantsForChat);
      console.log('[ProjectDetail.js] Chat link generated successfully:', response.data);
      setChatLink(response.data.chat_link);
      setSnackbarMessage('Chat link generated successfully!');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('[ProjectDetail.js] Error generating chat link:', error);
      setSnackbarMessage('Error generating chat link. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(chatLink);
    setSnackbarMessage('Link copied to clipboard');
    setSnackbarOpen(true);
  };

  const handleCloseLinkDialog = () => {
    setOpenLinkDialog(false);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  if (loading) {
    return <Typography>Loading project details...</Typography>;
  }

  if (!project) {
    return <Typography>Project not found</Typography>;
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            {project.name}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Created: {formatDate(project.created_at)}
          </Typography>
          <Box sx={{ mt: 1 }}>
            <Chip 
              label={project.status === 'active' ? 'Active' : 'Completed'} 
              color={project.status === 'active' ? 'success' : 'default'}
              size="small"
            />
          </Box>
        </Box>
        <Button 
          variant="contained" 
          startIcon={<LinkIcon />}
          onClick={handleGenerateChatLink}
        >
          Generate Chat Link
        </Button>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ minHeight: 200, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', boxShadow: 6, borderRadius: 4 }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', p: 3 }}>
              <PeopleIcon sx={{ fontSize: 56, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                Participants
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
              <Button size="large" variant="outlined" onClick={() => navigate(`/projects/${projectId}/participants`)}>
                Manage
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ minHeight: 200, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', boxShadow: 6, borderRadius: 4 }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', p: 3 }}>
              <QuestionAnswerIcon sx={{ fontSize: 56, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                Responses
              </Typography>
              <Typography variant="h3" component="div" sx={{ fontWeight: 700 }}>
                {project.responses_count}
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
              <Button size="large" variant="outlined" onClick={() => navigate(`/projects/${projectId}/responses`)}>
                View
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ minHeight: 200, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', boxShadow: 6, borderRadius: 4 }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', p: 3 }}>
              <VideoLibraryIcon sx={{ fontSize: 56, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                Topics
              </Typography>
              <Typography variant="h3" component="div" sx={{ fontWeight: 700 }}>
                {project.videos_count}
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
              <Button size="large" variant="outlined" component={Link} to={`/projects/${projectId}/topics`}>
                View
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ minHeight: 200, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', boxShadow: 6, borderRadius: 4 }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', p: 3 }}>
              <SummarizeIcon sx={{ fontSize: 56, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                Summary
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
              <Button size="large" variant="outlined" onClick={() => navigate(`/projects/${projectId}/summary`)}>
                View
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Project Description
      </Typography>
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="body1">
            {project.description || 'No description provided.'}
          </Typography>
        </CardContent>
      </Card>

      {/* Chat Link Dialog */}
      <Dialog open={openLinkDialog} onClose={handleCloseLinkDialog}>
        <DialogTitle>Chat Link Generated</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Share this link with your participants to collect their retrospective responses:
          </DialogContentText>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            mt: 2, 
            p: 2, 
            bgcolor: 'background.default',
            borderRadius: 1
          }}>
            <Typography sx={{ flexGrow: 1, wordBreak: 'break-all' }}>
              {chatLink}
            </Typography>
            <Button 
              startIcon={<ContentCopyIcon />} 
              onClick={handleCopyLink}
              sx={{ ml: 1 }}
            >
              Copy
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseLinkDialog}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default ProjectDetail;
