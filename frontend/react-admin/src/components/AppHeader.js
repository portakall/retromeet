import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Link from '@mui/material/Link';
import HomeIcon from '@mui/icons-material/Home';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { useLocation } from 'react-router-dom';

function AppHeader({ open, toggleDrawer, currentProject }) {
  const location = useLocation();
  const navigate = useNavigate();
  
  const pathSegments = location.pathname.split('/').filter(segment => segment);
  
  const getBreadcrumbs = () => {
    const breadcrumbs = [
      <Link
        underline="hover"
        sx={{ display: 'flex', alignItems: 'center' }}
        color="inherit"
        href="/"
        onClick={(e) => {
          e.preventDefault();
          navigate('/');
        }}
        key="home"
      >
        <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
        Home
      </Link>
    ];
    
    if (pathSegments.length > 0) {
      if (pathSegments[0] === 'projects') {
        breadcrumbs.push(
          <Link
            underline="hover"
            color="inherit"
            href="/projects"
            onClick={(e) => {
              e.preventDefault();
              navigate('/projects');
            }}
            key="projects"
          >
            Projects
          </Link>
        );
        
        if (pathSegments.length > 1) {
          breadcrumbs.push(
            <Typography color="text.primary" key="project-name">
              {currentProject ? currentProject.name : 'Project Details'}
            </Typography>
          );
          
          if (pathSegments.length > 2) {
            breadcrumbs.push(
              <Typography color="text.primary" key="section" sx={{ textTransform: 'capitalize' }}>
                {pathSegments[2]}
              </Typography>
            );
          }
        }
      } else {
        breadcrumbs.push(
          <Typography color="text.primary" key="section" sx={{ textTransform: 'capitalize' }}>
            {pathSegments[0]}
          </Typography>
        );
      }
    }
    
    return breadcrumbs;
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        transition: (theme) =>
          theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          onClick={toggleDrawer}
          edge="start"
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          RetroMeet Admin
        </Typography>
        <Breadcrumbs 
          separator={<NavigateNextIcon fontSize="small" />} 
          aria-label="breadcrumb"
          sx={{ 
            color: 'white',
            '& .MuiBreadcrumbs-separator': {
              color: 'rgba(255, 255, 255, 0.7)',
            },
            display: { xs: 'none', sm: 'flex' }
          }}
        >
          {getBreadcrumbs()}
        </Breadcrumbs>
      </Toolbar>
    </AppBar>
  );
}

export default AppHeader;
