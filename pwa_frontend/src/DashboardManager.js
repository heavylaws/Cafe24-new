import React, { useState, useEffect } from 'react';
import MenuManager from './components/MenuManager';
import CategoryManager from './components/CategoryManager';
import StockManager from './components/StockManager';
import DiscountManager from './components/DiscountManager';
import ReportsManager from './components/ReportsManager';
import UnitManager from './components/UnitManager';
import { 
  Tabs, Tab, Box, AppBar, Paper, Typography, Button, Container, Avatar,
  Switch, FormControlLabel, Grid, Card, CardContent, TextField, Snackbar, Alert, CircularProgress
} from '@mui/material';
import { 
  MenuBook, Category, Inventory, LocalOffer, Assessment, Settings, Science,
  Logout, LightMode, DarkMode 
} from '@mui/icons-material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

function SystemSettingsTab({ toggleTheme, isDarkMode }) {
  const [settings, setSettings] = useState({
    exchange_rate: 1500,
    default_currency: 'USD'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/v1/system-settings`, {
        headers: getAuthHeader()
      });
      if (!response.ok) throw new Error('Failed to fetch settings');
      const data = await response.json();
      setSettings(data);
    } catch (err) {
      setError('Failed to fetch system settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/v1/system-settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(settings)
      });

      if (!response.ok) throw new Error('Failed to save settings');
      
      setSuccess('Settings saved successfully!');
    } catch (err) {
      setError('Failed to save settings');
    }
  };

  if (loading) return <CircularProgress />;

  return (
    <Paper elevation={3} sx={{ p: 3, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Settings sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>System Settings</Typography>
        </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card elevation={2} sx={{ p: 2, borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Currency Settings</Typography>
              <TextField
                label="Exchange Rate (USD to LBP)"
                type="number"
                fullWidth
                value={settings.exchange_rate}
                onChange={(e) => setSettings({ ...settings, exchange_rate: parseFloat(e.target.value) || 0 })}
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.01 }}
              />
              <Button variant="contained" onClick={handleSave} fullWidth sx={{ borderRadius: 25 }}>
                Save Rate
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card elevation={2} sx={{ p: 2, borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Display Settings</Typography>
              <FormControlLabel
                control={<Switch checked={isDarkMode} onChange={toggleTheme} />}
                label={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError('')}>
        <Alert onClose={() => setError('')} severity="error">{error}</Alert>
      </Snackbar>
      <Snackbar open={!!success} autoHideDuration={4000} onClose={() => setSuccess('')}>
        <Alert onClose={() => setSuccess('')} severity="success">{success}</Alert>
      </Snackbar>
    </Paper>
  );
}


function DashboardManager({ user, onLogout }) {
  const [tab, setTab] = useState(0);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const theme = createTheme({
    palette: {
      mode: isDarkMode ? 'dark' : 'light',
      primary: {
        main: '#673ab7',
      },
      secondary: {
        main: '#f50057',
      },
      background: {
        default: isDarkMode ? '#121212' : '#f4f6f8',
        paper: isDarkMode ? '#1e1e1e' : '#ffffff',
      },
    },
    typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                }
            }
        }
    }
  });
  
  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  const tabs = [
    { label: "Menu Items", icon: <MenuBook /> },
    { label: "Categories", icon: <Category /> },
    { label: "Stock", icon: <Inventory /> },
    { label: "Units", icon: <Science /> },
    { label: "Discounts", icon: <LocalOffer /> },
    { label: "Reports", icon: <Assessment /> },
    { label: "Settings", icon: <Settings /> }
  ];

  return (
    <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>

            {/* Main Content */}
            <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
                {/* Header */}
                <Paper elevation={3} sx={{ 
                    p: 2, 
                    mb: 3,
                    borderRadius: 3,
        display: 'flex',
        justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <Box>
                        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                            Manager Dashboard
                        </Typography>
                        <Typography variant="h6" color="text.secondary">
                            Welcome, {user.full_name || user.username}!
                        </Typography>
                    </Box>
                    <Button 
            onClick={onLogout} 
                        variant="contained"
                        color="secondary"
                        startIcon={<Logout />}
          >
            Logout
                    </Button>
                </Paper>

                {/* Tabs */}
                <Paper elevation={3} sx={{ borderRadius: 3, overflow: 'hidden' }}>
                    <AppBar position="static" color="default" elevation={0}>
                        <Tabs
                            value={tab}
                            onChange={handleTabChange}
                            indicatorColor="primary"
                            textColor="primary"
                            variant="scrollable"
                            scrollButtons="auto"
                        >
                        {tabs.map((tabItem, index) => (
                            <Tab 
                                key={index}
                                label={tabItem.label} 
                                icon={tabItem.icon}
                                iconPosition="start"
                                sx={{ py: 2, px: 3 }}
                            />
                        ))}
                        </Tabs>
                    </AppBar>
                    
                    <Box sx={{ p: 3, minHeight: '60vh' }}>
                        {tab === 0 && <MenuManager />}
                        {tab === 1 && <CategoryManager />}
                        {tab === 2 && <StockManager />}
                        {tab === 3 && <UnitManager />}
                        {tab === 4 && <DiscountManager />}
                        {tab === 5 && <ReportsManager />}
                        {tab === 6 && <SystemSettingsTab toggleTheme={toggleTheme} isDarkMode={isDarkMode} />}
                    </Box>
                </Paper>
            </Box>
        </Box>
    </ThemeProvider>
  );
}

export default DashboardManager;
