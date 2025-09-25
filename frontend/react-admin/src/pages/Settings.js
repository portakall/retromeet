import React from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

function Settings() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings Page
      </Typography>
      <Typography variant="body1" sx={{ mt: 2, mb: 2 }}>
        Here you’ll be able to manage your account preferences, notification settings, and other personal options. We’re working hard to bring you these features soon!
      </Typography>
      <Typography variant="h6" component="p" color="warning.main" sx={{ mb: 2 }}>
        ⚠️ This page is under construction.
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Please check back later for updates. Have suggestions? Contact support!
      </Typography>
    </Box>
  );
}

export default Settings;
