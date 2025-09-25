import React from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

function Help() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Help
      </Typography>
      <Typography variant="body1" sx={{ maxWidth: 600, textAlign: 'center' }}>
        Welcome to the RetroMeet admin panel!<br /><br />
        <b>How to use:</b><br />
        - Use the sidebar to navigate between dashboard, projects, participants, and other features.<br />
        - If you need to manage project details, use the Projects section.<br />
        - For participant and response management, select a project first.<br /><br />
        If you encounter any issues or have questions, please contact your system administrator or check the project documentation.<br /><br />
        <i>This help page is under construction and will be updated with more information soon.</i>
      </Typography>
    </Box>
  );
}

export default Help;
