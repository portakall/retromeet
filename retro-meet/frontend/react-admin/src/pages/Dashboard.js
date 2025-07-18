import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import AddIcon from '@mui/icons-material/Add';
import FolderIcon from '@mui/icons-material/Folder';
import PeopleIcon from '@mui/icons-material/People';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import { getProjects } from '../services/api';

function Dashboard({ setCurrentProject }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        // In a real implementation, we would call the API
        // const response = await getProjects();
        // setProjects(response.data);
        
        // For now, use mock data
        setProjects([
          { id: 1, name: 'Sprint Retrospective - May 2025', participants_count: 5, responses_count: 15, videos_count: 8 },
          { id: 2, name: 'Product Review - Q2 2025', participants_count: 3, responses_count: 9, videos_count: 4 }
        ]);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching projects:', error);
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  const handleProjectClick = (project) => {
    setCurrentProject(project);
    navigate(`/projects/${project.id}`);
  };

  const handleCreateProject = () => {
    navigate('/projects/new');
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>

      </Box>

      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        Recent Projects
      </Typography>

      {loading ? (
        <Typography>Loading projects...</Typography>
      ) : projects.length > 0 ? (
        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <Card 
                sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column',
                  transition: 'transform 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-5px)',
                  }
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                    <FolderIcon sx={{ fontSize: 60, color: 'primary.main' }} />
                  </Box>
                  <Typography variant="h6" component="h2" gutterBottom noWrap>
                    {project.name}
                  </Typography>
                  <Grid container spacing={2} sx={{ mt: 2 }}>
                    <Grid item xs={4}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <PeopleIcon color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {project.participants_count} Participants
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <QuestionAnswerIcon color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {project.responses_count} Responses
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <VideoLibraryIcon color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {project.videos_count} Videos
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    fullWidth
                    onClick={() => handleProjectClick(project)}
                  >
                    View Project
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" gutterBottom>
            No projects found. Create your first project to get started.
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={handleCreateProject}
            sx={{ mt: 2 }}
          >
            Create Project
          </Button>
        </Box>
      )}
    </Box>
  );
}

export default Dashboard;
