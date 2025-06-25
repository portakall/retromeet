import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import Divider from '@mui/material/Divider';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FolderIcon from '@mui/icons-material/Folder';
import PeopleIcon from '@mui/icons-material/People';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import TopicIcon from '@mui/icons-material/Topic';
import SummarizeIcon from '@mui/icons-material/Summarize';
import SettingsIcon from '@mui/icons-material/Settings';
import HelpIcon from '@mui/icons-material/Help';

const drawerWidth = 240;

function Sidebar({ open, toggleDrawer }) {
  const navigate = useNavigate();
  const location = useLocation();
  
  const isProjectRoute = location.pathname.includes('/projects/') && location.pathname.split('/').length > 3;
  const projectId = isProjectRoute ? location.pathname.split('/')[2] : null;

  const mainMenuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Projects', icon: <FolderIcon />, path: '/projects' },
  ];

  const projectMenuItems = projectId ? [
    { text: 'Participants', icon: <PeopleIcon />, path: `/projects/${projectId}/participants` },
    { text: 'Responses', icon: <QuestionAnswerIcon />, path: `/projects/${projectId}/responses` },
    { text: 'Topics', icon: <TopicIcon />, path: `/projects/${projectId}/topics` },
    { text: 'Summary', icon: <SummarizeIcon />, path: `/projects/${projectId}/summary` },
  ] : [];

  const bottomMenuItems = [
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
    { text: 'Help', icon: <HelpIcon />, path: '/help' },
  ];

  const handleNavigation = (path) => {
    navigate(path);
  };

  const drawer = (
    <>
      <Box sx={{ overflow: 'auto', mt: 8 }}>
        <List>
          {mainMenuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton 
                selected={location.pathname === item.path}
                onClick={() => handleNavigation(item.path)}
              >
                <ListItemIcon>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        
        {projectId && (
          <>
            <Divider />
            <List>
              {projectMenuItems.map((item) => (
                <ListItem key={item.text} disablePadding>
                  <ListItemButton 
                    selected={location.pathname === item.path}
                    onClick={() => handleNavigation(item.path)}
                  >
                    <ListItemIcon>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText primary={item.text} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </>
        )}
        
        <Divider />
        <List>
          {bottomMenuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton 
                selected={location.pathname === item.path}
                onClick={() => handleNavigation(item.path)}
              >
                <ListItemIcon>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </>
  );

  return (
    <Drawer
      variant="persistent"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      {drawer}
    </Drawer>
  );
}

export default Sidebar;
