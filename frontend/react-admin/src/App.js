import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

// Components
import AppHeader from './components/AppHeader';
import Sidebar from './components/Sidebar';

// Pages
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Participants from './pages/Participants';
import Responses from './pages/Responses';
import Topics from './pages/Topics';
import Summary from './pages/Summary';

const theme = createTheme({
  palette: {
    primary: {
      main: '#6c5ce7',
    },
    secondary: {
      main: '#a29bfe',
    },
    background: {
      default: '#f8f9fa',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 500,
    },
    h2: {
      fontWeight: 500,
    },
    h3: {
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },
  },
});

function App() {
  const [open, setOpen] = useState(true);
  const [currentProject, setCurrentProject] = useState(null);
  
  const toggleDrawer = () => {
    setOpen(!open);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex' }}>
        <AppHeader open={open} toggleDrawer={toggleDrawer} currentProject={currentProject} />
        <Sidebar open={open} toggleDrawer={toggleDrawer} />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            mt: 8,
            width: { sm: `calc(100% - ${open ? 240 : 0}px)` },
            ml: { sm: open ? 0 : 0 },
            transition: theme.transitions.create(['margin', 'width'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard setCurrentProject={setCurrentProject} />} />
            <Route path="/projects" element={<Projects setCurrentProject={setCurrentProject} />} />
            <Route path="/projects/:projectId" element={<ProjectDetail setCurrentProject={setCurrentProject} />} />
            <Route path="/projects/:projectId/participants" element={<Participants />} />
            <Route path="/projects/:projectId/responses" element={<Responses />} />
            <Route path="/projects/:projectId/topics" element={<Topics />} />
            <Route path="/projects/:projectId/summary" element={<Summary />} />
          </Routes>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
