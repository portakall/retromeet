import React, { useState } from 'react';
import { Box, Typography, Button, CircularProgress, List, ListItem, ListItemText, Paper, Alert, Dialog, DialogActions, DialogContent, DialogTitle, Card, CardHeader, CardContent, Avatar, Chip } from '@mui/material';
import TopicIcon from '@mui/icons-material/Topic';
import { useParams } from 'react-router-dom';
import { generateTopics, getResponsesForTopic } from '../services/api';

function Topics() {
  const { projectId } = useParams();
  const [loading, setLoading] = useState(false);
  const [topics, setTopics] = useState([]);
  const [error, setError] = useState(null);

  // New state for topic responses modal
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topicResponses, setTopicResponses] = useState([]);
  const [topicResponsesLoading, setTopicResponsesLoading] = useState(false);
  const [topicResponsesError, setTopicResponsesError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleGenerateTopics = async () => {
    setLoading(true);
    setError(null);
    setTopics([]);
    // Close modal if it's open from a previous generation
    setIsModalOpen(false); 
    setSelectedTopic(null);
    setTopicResponses([]);
    try {
      const response = await generateTopics(projectId);
      setTopics(response.data || []);
      if (!response.data || response.data.length === 0) {
        setError("No topics were generated, or the list was empty.");
      }
    } catch (err) {
      setError('Failed to generate topics. Please try again.');
      console.error('Error generating topics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTopicClick = async (topic) => {
    setSelectedTopic(topic);
    setIsModalOpen(true);
    setTopicResponsesLoading(true);
    setTopicResponsesError(null);
    setTopicResponses([]);
    try {
      const response = await getResponsesForTopic(projectId, topic);
      setTopicResponses(response.data || []);
    } catch (err) {
      setTopicResponsesError('Failed to fetch responses for this topic.');
      console.error('Error fetching topic responses:', err);
    } finally {
      setTopicResponsesLoading(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Discussion Topics
      </Typography>
      <Typography variant="body1" paragraph>
        Generate discussion topics from participant responses. Click on a topic to see related comments.
      </Typography>
      <Button 
        variant="contained" 
        color="primary" 
        startIcon={<TopicIcon />}
        onClick={handleGenerateTopics}
        disabled={loading}
        sx={{ mb: 2 }}
      >
        {loading ? <CircularProgress size={24} /> : 'Generate Topics'}
      </Button>

      {error && (
        <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
          {error}
        </Alert>
      )}

      {topics.length > 0 && (
        <Paper elevation={3} sx={{ mt: 2 }}>
          <List>
            {topics.map((topic, index) => (
              <ListItem 
                key={index} 
                button 
                onClick={() => handleTopicClick(topic)}
                divider={index < topics.length - 1}
              >
                <ListItemText primary={topic} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Modal for Topic Responses */}
      <Dialog open={isModalOpen} onClose={handleCloseModal} fullWidth maxWidth="md" scroll="paper">
        <DialogTitle>
          Responses for: "{selectedTopic}"
        </DialogTitle>
        <DialogContent dividers>
          {topicResponsesLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
              <CircularProgress />
            </Box>
          )}
          {topicResponsesError && (
            <Alert severity="error" sx={{ my: 2 }}>{topicResponsesError}</Alert>
          )}
          {!topicResponsesLoading && !topicResponsesError && (
            topicResponses.length > 0 ? (
              <List sx={{ pt: 0 }}>
                {topicResponses.map((resp) => (
                  <Card key={resp.participant_id} sx={{ mb: 2, '&:last-child': { mb: 0 } }} variant="outlined">
                    <CardHeader
                      avatar={
                        <Avatar 
                          src={resp.participant_avatar_path || `/static/avatars/default.png`} 
                          alt={resp.participant_name || 'Participant'}
                          sx={{ bgcolor: resp.participant_avatar_path ? 'transparent' : 'primary.main' }}
                        >
                          {/* Fallback to first letter if src is invalid or not provided */}
                          {!resp.participant_avatar_path && (resp.participant_name ? resp.participant_name.charAt(0).toUpperCase() : '?')}
                        </Avatar>
                      }
                      title={resp.participant_name || 'Unknown Participant'}
                      subheader={`Participant ID: ${resp.participant_id}`}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <Typography variant="subtitle2" gutterBottom sx={{ color: 'text.secondary' }}>
                        Relevant Snippets:
                      </Typography>
                      {resp.relevant_snippets && resp.relevant_snippets.length > 0 ? (
                        <List dense disablePadding>
                          {resp.relevant_snippets.map((snippet, idx) => (
                            <ListItem key={idx} sx={{ display: 'flex', alignItems: 'flex-start', py: 0.5, pl:0 }}>
                              <Chip label={idx + 1} size="small" sx={{ mr: 1.5, mt: 0.5, bgcolor: 'action.hover' }} />
                              <ListItemText 
                                primaryTypographyProps={{ variant: 'body2' }}
                                primary={snippet} 
                              />
                            </ListItem>
                          ))}
                        </List>
                      ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                          No specific snippets extracted for this topic from this participant.
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </List>
            ) : (
              <Typography sx={{ my: 2, textAlign: 'center', color: 'text.secondary' }}>
                No participants found who discussed this topic, or no relevant snippets were extracted.
              </Typography>
            )
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseModal} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Topics;
