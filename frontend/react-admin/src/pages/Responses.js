import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import RefreshIcon from '@mui/icons-material/Refresh';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Avatar from '@mui/material/Avatar';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw'; // For rendering HTML tags in markdown
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import { getProjectResponses, getProject } from '../services/api';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`responses-tabpanel-${index}`}
      aria-labelledby={`responses-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function Responses() {
  // ...existing state
  const [tunedModal, setTunedModal] = useState({ open: false, participant: null, tunedResponse: null });

  // Handler to open modal with participant and tuned response
  const handleOpenTunedModal = (participant, tunedResponse) => {
    setTunedModal({ open: true, participant, tunedResponse });
  };
  // Handler to close modal
  const handleCloseTunedModal = () => {
    setTunedModal({ open: false, participant: null, tunedResponse: null });
  };

  const { projectId } = useParams();
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [groupedResponses, setGroupedResponses] = useState({
    byParticipant: {},
    byQuestion: {}
  });

  const [project, setProject] = useState({});

  const [refreshKey, setRefreshKey] = useState(0); // Add a key to trigger refresh

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await getProject(projectId);
        setProject(response.data);
      } catch (error) {
        console.error('Error fetching project:', error);
      }
    };

    fetchProject();
  }, [projectId]);

  const fetchResponses = async () => {
      try {
        setLoading(true);
        const response = await getProjectResponses(projectId);
        
        if (response.data && Array.isArray(response.data)) {
          const responsesWithFullContent = await Promise.all(
            response.data.map(async (resp) => {
              // If it's a chat response, fetch the full content and overwrite original_response
              if (resp.chat_response_file_path) {
                try {
                  const fileResponse = await fetch(`http://localhost:8000/static/${resp.chat_response_file_path}`);
                  if (fileResponse.ok) {
                    const markdownContent = await fileResponse.text();
                    // Return the response with original_response updated, but keep other fields like refined_response
                    return { ...resp, original_response: markdownContent }; 
                  } else {
                     // If fetch fails, just return the original response data
                     console.error(`Error fetching chat content for ${resp.chat_response_file_path}: ${fileResponse.statusText}`);
                     return resp;
                  }
                } catch (error) {
                  console.error(`Error fetching chat content for ${resp.chat_response_file_path}`, error);
                  return resp; // On error, return original response
                }
              }
              // If it's not a chat response, just return it as is.
              return resp;
            })
          );

          const processedResponses = responsesWithFullContent.map(resp => {
            const pName = resp.participant_name || `Participant ${resp.participant_id || 'Unknown'}`;
            // Use the avatar_path from the backend response if available (e.g., resp.participant_avatar_path)
            // or a default if not present.
            const backendAvatarPath = resp.participant_avatar_path; // Adjust field name if necessary
            return {
              ...resp,
              participant: {
                id: resp.participant_id,
                name: pName,
                avatar_path: backendAvatarPath || `/static/avatars/default.png` // Use backend path or default
              }
            };
          });
          
          setResponses(processedResponses);

          const byParticipant = {};
          const byQuestion = {};

          processedResponses.forEach(transformedResp => {
            const participantNameKey = transformedResp.participant.name;
            if (!byParticipant[participantNameKey]) {
              byParticipant[participantNameKey] = {
                participant: transformedResp.participant,
                responses: []
              };
            }
            byParticipant[participantNameKey].responses.push(transformedResp);

            const questionKey = transformedResp.question || "General Feedback";
            if (!byQuestion[questionKey]) {
              byQuestion[questionKey] = [];
            }
            byQuestion[questionKey].push(transformedResp);
          });
          
          setGroupedResponses({ byParticipant, byQuestion });
        } else {
          setResponses([]);
          setGroupedResponses({ byParticipant: {}, byQuestion: {} });
        }
      } catch (error) {
        console.error('Error fetching responses:', error);
      } finally {
        setLoading(false);
      }
    };

  useEffect(() => {
    fetchResponses();
  }, [projectId, refreshKey]); // Add refreshKey to trigger refetch

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };



  const formatDate = (dateString) => {
    if (!dateString) {
      return 'No date';
    }
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid date';
      }
      
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Invalid date';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 0 }}>
          {project.name} Responses
        </Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={() => setRefreshKey(oldKey => oldKey + 1)}
        >
          Refresh
        </Button>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Chip label={project.status} color="primary" />
        <Typography variant="body2" color="text.secondary">
          Created by {project.creator_name} on {formatDate(project.created_at)}
        </Typography>
      </Box>
      <Divider sx={{ mb: 4 }} />

      {loading ? (
        <Typography>Loading responses...</Typography>
      ) : responses.length > 0 ? (
        <Box sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="responses tabs">
              <Tab label="By Participant" />
              <Tab label="By Question" />
              <Tab label="Tuned Responses" />
            </Tabs>
          </Box>
          
          {/* By Participant View */}
          <TabPanel value={tabValue} index={0}>
            {Object.values(groupedResponses.byParticipant).map((participantData, index) => (
              <Accordion key={participantData.participant?.id || `participant-${index}`}>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`participant-${participantData.participant?.id || index}-content`}
                  id={`participant-${participantData.participant?.id || index}-header`}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar 
                      src={participantData.participant?.avatar_path || `/static/avatars/default.png`}
                      alt={participantData.participant?.name || 'Participant'}
                      sx={{ mr: 2 }}
                    >
                      {(participantData.participant?.name || 'P').charAt(0)}
                    </Avatar>
                    <Typography variant="h6">{participantData.participant?.name || 'Unknown Participant'}</Typography>
                    <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                      {(participantData.responses || []).length} responses
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={3}>
                    {(participantData.responses || []).map((response) => (
                      <Grid item xs={12} key={response.id}>
                        <Card sx={{ mb: 2, border: 1, borderColor: 'grey.200' }}>
                          <CardHeader
                            title={response.question}
                            subheader={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" color="text.secondary">
                                  {formatDate(response.created_at)}
                                </Typography>
                                <Chip 
                                  label={`Project ${projectId}`} 
                                  size="small" 
                                  variant="outlined"
                                  sx={{ fontSize: '0.75rem' }}
                                />
                              </Box>
                            }
                          />
                          <CardContent>
                            <Paper 
                              elevation={0} 
                              sx={{ 
                                p: 2, 
                                bgcolor: 'background.default',
                                borderRadius: 1
                              }}
                            >
                              <div className="markdown-content">
                                <ReactMarkdown>{response.original_response}</ReactMarkdown>
                              </div>
                            </Paper>
                            {response.chat_response_file_path && (
                              <Box sx={{ mt: 2 }}>
                                <Button
                                  variant="outlined"
                                  size="small"

                                >
                                  View Full Chat Response
                                </Button>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </TabPanel>
          
          {/* By Question View */}
          <TabPanel value={tabValue} index={1}>
            {Object.entries(groupedResponses.byQuestion).map(([question, questionResponses]) => (
              <Accordion key={question}>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`question-${question.replace(/\s+/g, '-')}-content`}
                  id={`question-${question.replace(/\s+/g, '-')}-header`}
                >
                  <Box>
                    <Typography variant="h6">{question}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {questionResponses.length} responses
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={3}>
                    {questionResponses.map((response) => (
                      <Grid item xs={12} md={6} key={response.id}>
                        <Card sx={{ mb: 2, border: 1, borderColor: 'grey.200' }}>
                          <CardHeader
                            avatar={
                              <Avatar 
                                src={response.participant.avatar_path}
                                alt={response.participant.name}
                              >
                                {response.participant.name.charAt(0)}
                              </Avatar>
                            }
                            title={response.participant.name}
                            subheader={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" color="text.secondary">
                                  {formatDate(response.created_at)}
                                </Typography>
                                <Chip 
                                  label={`Project ${projectId}`} 
                                  size="small" 
                                  variant="outlined"
                                  sx={{ fontSize: '0.75rem' }}
                                />
                              </Box>
                            }
                          />
                          <CardContent>
                            <Paper 
                              elevation={0} 
                              sx={{ 
                                p: 2, 
                                bgcolor: 'background.default',
                                borderRadius: 1
                              }}
                            >
                              <div className="markdown-content">
                                <ReactMarkdown>{response.original_response}</ReactMarkdown>
                              </div>
                            </Paper>
                            {response.chat_response_file_path && (
                              <Box sx={{ mt: 2 }}>
                                <Button
                                  variant="outlined"
                                  size="small"

                                >
                                  View Full Chat Response
                                </Button>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </TabPanel>
          
          {/* Tuned Responses View */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              {Object.values(groupedResponses.byParticipant).map((participantData) => {
                const tunedResponse = participantData.responses.find(r => r.refined_response);
                const participant = participantData.participant;

                return (
                  <Grid item xs={12} md={6} key={participant.id}>
                    <Card
                      sx={{
                        mb: 2,
                        border: 1,
                        borderColor: 'grey.200',
                        boxShadow: 3,
                        borderRadius: 3,
                        cursor: tunedResponse ? 'pointer' : 'default',
                        transition: 'transform 0.2s',
                        '&:hover': tunedResponse ? { transform: 'scale(1.03)', boxShadow: 6 } : {},
                        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                      }}
                      onClick={() => tunedResponse && handleOpenTunedModal(participant, tunedResponse)}
                    >
                      <CardHeader
                        avatar={
                          <Avatar
                            src={participant.avatar_path || `/static/avatars/default.png`}
                            alt={participant.name}
                            sx={{ width: 64, height: 64, fontSize: 32, border: '2px solid #90caf9', bgcolor: '#e3f2fd' }}
                          >
                            {participant.name.charAt(0)}
                          </Avatar>
                        }
                        title={<Typography variant="h6" sx={{ fontWeight: 600 }}>{participant.name}</Typography>}
                        subheader={<Typography variant="subtitle2" color="primary">Tuned Speech</Typography>}
                      />
                      <CardContent>
                        <Paper
                          elevation={0}
                          sx={{
                            p: 2,
                            bgcolor: 'background.paper',
                            borderRadius: 2,
                            minHeight: 120,
                          }}
                        >
                          <div className="markdown-content" style={{ fontSize: '1.1rem', color: '#222' }}>
                            <ReactMarkdown>
                              {tunedResponse ? tunedResponse.refined_response : '*No tuned response generated yet.*'}
                            </ReactMarkdown>
                          </div>
                        </Paper>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}

              {/* Tuned Response Modal */}
              <Dialog
                open={Boolean(tunedModal.open)}
                onClose={handleCloseTunedModal}
                maxWidth="md"
                fullWidth
                PaperProps={{
                  sx: {
                    borderRadius: 4,
                    p: 4,
                    bgcolor: 'background.default',
                    boxShadow: 12,
                  }
                }}
              >
                {tunedModal.participant && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
                    <Avatar
                      src={tunedModal.participant.avatar_path || `/static/avatars/default.png`}
                      alt={tunedModal.participant.name}
                      sx={{
                        width: 180,
                        height: 180,
                        fontSize: 90,
                        mb: 3,
                        border: '6px solid #1976d2',
                        bgcolor: '#e3f2fd',
                        boxShadow: 8,
                        transition: 'transform 0.2s',
                        '&:hover': { transform: 'scale(1.05)' },
                      }}
                    >
                      {tunedModal.participant.name.charAt(0)}
                    </Avatar>
                    <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>{tunedModal.participant.name}</Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>Tuned Speech</Typography>
                  </Box>
                )}
                <Paper elevation={0} sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 3 }}>
                  <div
                    className="markdown-content tuned-markdown"
                    style={{
                      fontSize: '1.25rem',
                      color: '#1a1a1a',
                      lineHeight: 1.8,
                      letterSpacing: '0.01em',
                      maxWidth: 700,
                      margin: '0 auto',
                      padding: '8px 0',
                    }}
                  >
                    <ReactMarkdown
                      rehypePlugins={[rehypeRaw]} // Allow rendering HTML tags (like <span>) in markdown
                      components={{
                        p: ({ node, ...props }) => <p style={{ marginBottom: 24, marginTop: 0 }}>{props.children}</p>,
                      }}
                    >
                      {tunedModal.tunedResponse ?
                        (() => {
                          const text = tunedModal.tunedResponse.refined_response || '';
                          const firstParagraphMatch = text.match(/^(.*?)(\n|$)/);
                          if (!firstParagraphMatch) return text;
                          const firstParagraph = firstParagraphMatch[1];
                          const rest = text.slice(firstParagraph.length);
                          if (!firstParagraph) return text;
                          return `
<span style="font-size:1.5rem;line-height:1;margin-right:2px;font-weight:bold;color:#1976d2;vertical-align:baseline;display:inline-block;">${firstParagraph.charAt(0)}</span>${firstParagraph.slice(1)}${rest}
`;
                        })()
                        : '*No tuned response generated yet.*'}
                    </ReactMarkdown>
                  </div>
                </Paper>
                <DialogActions sx={{ mt: 2 }}>
                  <Button onClick={handleCloseTunedModal} color="primary" variant="contained" sx={{ minWidth: 120 }}>
                    Close
                  </Button>
                </DialogActions>
              </Dialog>

            </Grid>
          </TabPanel>
        </Box>
      ) : (
        <Paper sx={{ textAlign: 'center', py: 8, px: 4, bgcolor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            No responses collected yet for {project.name || 'this project'}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Share the chat link with participants to start collecting retrospective responses.
          </Typography>
          <Chip 
            label={`Project ID: ${projectId}`} 
            variant="outlined" 
            size="small"
            sx={{ opacity: 0.7 }}
          />
        </Paper>
      )}
    </Box>
  );
}

export default Responses;
