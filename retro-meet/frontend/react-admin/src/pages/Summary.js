import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import AssignmentIcon from '@mui/icons-material/Assignment';
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import ReactMarkdown from 'react-markdown';
import { generateSummary, getSummary } from '../services/api';

function Summary() {
  const { projectId } = useParams();
  const [summary, setSummary] = useState(null);
const [editingActionItems, setEditingActionItems] = useState([]);
const [actionItemsChanged, setActionItemsChanged] = useState(false);
  const [loading, setLoading] = useState(false); // Start with no loading, summary is null
  const [generating, setGenerating] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  const [projectName, setProjectName] = useState('');

  useEffect(() => {
    // Fetch project name
    async function fetchProject() {
      try {
        const res = await import('../services/api');
        const { getProject } = res;
        const response = await getProject(projectId);
        setProjectName(response.data.name || '');
      } catch (error) {
        setProjectName('');
      }
    }
    fetchProject();
  }, [projectId]);

    // useEffect will not fetch summary on initial load.
  // Summary will be fetched when 'Regenerate Summary' is clicked.
  // If you want to load a previously saved summary, you would call getSummary here.
  // For now, we start with a blank page for summary content.
  useEffect(() => {
    // Optional: If you implement getSummary and want to load on mount:
    // const loadInitialSummary = async () => {
    //   setLoading(true);
    //   try {
    //     const response = await getSummary(projectId); // Assuming getSummary fetches the new JSON structure
    //     if (response.data) {
    //       setSummary(response.data);
    //       setSnackbarMessage('Summary loaded');
    //       setSnackbarSeverity('info');
    //       setSnackbarOpen(true);
    //     } else {
    //       setSummary(null); // Ensure summary is null if no data
    //     }
    //   } catch (error) {
    //     if (error.response && error.response.status === 404) {
    //       setSummary(null); // No summary found, which is fine initially
    //       console.log('No pre-existing summary found.');
    //     } else {
    //       console.error('Error fetching initial summary:', error);
    //       setSnackbarMessage('Failed to load existing summary');
    //       setSnackbarSeverity('error');
    //       setSnackbarOpen(true);
    //     }
    //   }
    //   setLoading(false);
    // };
    // loadInitialSummary();
  }, [projectId]);

  const handleGenerateSummary = async () => {
    setGenerating(true);
    setSummary(null); // Clear previous summary before generating a new one
    try {
      const response = await generateSummary(projectId); // API call
      setSummary(response.data); // response.data should be the structured JSON
      setEditingActionItems(response.data.action_items.map((item, idx) => ({ ...item, _tmpId: idx })));
      setActionItemsChanged(false);
      setSnackbarMessage('Summary generated successfully');
      setSnackbarSeverity('success');
    } catch (error) {
      console.error('Error generating summary:', error);
      let message = 'Failed to generate summary.';
      if (error.response && error.response.data && error.response.data.detail) {
        message = typeof error.response.data.detail === 'string' ? error.response.data.detail : JSON.stringify(error.response.data.detail);
      }
      setSnackbarMessage(message);
      setSnackbarSeverity('error');
    } finally {
      setGenerating(false);
      setSnackbarOpen(true);
    }
  };

  const handleDownloadSummary = () => {
    if (!summary) return;
    
    const content = `
# ${summary.title}

${summary.overview}

${summary.key_themes || '## Key Themes\n\nNot available.'}

${summary.positives}

${summary.improvements}

## Action Items

${summary.action_items.map(item => `- ${item.description} (Priority: ${item.priority})`).join('\n')}

Generated at: ${new Date().toLocaleString()} (Note: 'generated_at' from backend not directly used here, assuming fresh download)
    `;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${summary.title.replace(/\s+/g, '-').toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'completed':
        return <Chip label="Completed" color="success" size="small" />;
      case 'in_progress':
        return <Chip label="In Progress" color="primary" size="small" />;
      case 'pending':
        return <Chip label="Pending" color="warning" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {projectName ? `${projectName} Sprint Summary` : 'Sprint Summary'}
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={handleGenerateSummary}
            disabled={generating}
            sx={{ mr: 2 }}
          >
            {generating ? <CircularProgress size={24} /> : 'Regenerate Summary'}
          </Button>
          <Button 
            variant="contained" 
            startIcon={<DownloadIcon />}
            onClick={handleDownloadSummary}
            disabled={!summary || generating}
          >
            Download Summary
          </Button>
        </Box>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : summary ? (
        <>
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                {summary.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {/* Generated on: {new Date(summary.generated_at).toLocaleString()} */}
              {/* We don't get generated_at from the new backend structure for the main summary object, but can add if needed */}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <div className="markdown-content">
                <ReactMarkdown>{summary.overview}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>

          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">What Went Well</Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <div className="markdown-content">
                  <ReactMarkdown>{summary.positives}</ReactMarkdown>
                </div>
              </Paper>
            </Grid>

            {/* Key Themes Section */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LightbulbIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Key Themes</Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <div className="markdown-content">
                  <ReactMarkdown>{summary.key_themes || "No key themes identified."}</ReactMarkdown>
                </div>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <WarningIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">What Could Be Improved</Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <div className="markdown-content">
                  <ReactMarkdown>{summary.improvements}</ReactMarkdown>
                </div>
              </Paper>
            </Grid>
          </Grid>

          <Box sx={{ mt: 4 }}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AssignmentIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Action Items</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List>
                {editingActionItems.map((item, idx) => (
                  <ListItem key={item._tmpId} divider secondaryAction={
                    <IconButton edge="end" aria-label="delete" onClick={() => {
                      setEditingActionItems(editingActionItems.filter((_, i) => i !== idx));
                      setActionItemsChanged(true);
                    }}>
                      <ErrorIcon color="error" />
                    </IconButton>
                  }>
                    <ListItemIcon>
                      <LightbulbIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <TextField
                          variant="standard"
                          value={item.description}
                          onChange={e => {
                            const newItems = [...editingActionItems];
                            newItems[idx].description = e.target.value;
                            setEditingActionItems(newItems);
                            setActionItemsChanged(true);
                          }}
                          fullWidth
                        />
                      }
                      secondary={
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                          <TextField
                            label="Priority"
                            variant="outlined"
                            size="small"
                            value={item.priority}
                            onChange={e => {
                              const newItems = [...editingActionItems];
                              newItems[idx].priority = e.target.value;
                              setEditingActionItems(newItems);
                              setActionItemsChanged(true);
                            }}
                            sx={{ width: 120 }}
                          />
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  disabled={!actionItemsChanged}
                  onClick={async () => {
                    try {
                      const updatedSummary = { ...summary, action_items: editingActionItems.map(({_tmpId, ...rest}) => rest) };
                      await import('../services/api').then(({ updateSummary }) => updateSummary(projectId, updatedSummary));
                      setSummary(updatedSummary);
                      setActionItemsChanged(false);
                      setSnackbarMessage('Action Items updated successfully');
                      setSnackbarSeverity('success');
                      setSnackbarOpen(true);
                    } catch (error) {
                      setSnackbarMessage('Failed to update Action Items');
                      setSnackbarSeverity('error');
                      setSnackbarOpen(true);
                    }
                  }}
                >
                  Save
                </Button>
              </Box>
            </Paper>
          </Box>
        </>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" gutterBottom>
            No summary has been generated yet for this project.
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<RefreshIcon />}
            onClick={handleGenerateSummary}
            disabled={generating}
            sx={{ mt: 2 }}
          >
            {generating ? <CircularProgress size={24} /> : 'Generate Summary'}
          </Button>
        </Box>
      )}

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

export default Summary;
