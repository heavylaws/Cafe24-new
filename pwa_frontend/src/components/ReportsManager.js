import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Tabs, Tab, Grid, Card, CardContent, Button,
  TextField, Select, MenuItem, FormControl, InputLabel, Alert, CircularProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Avatar
} from '@mui/material';
import { 
  TrendingUp, AttachMoney, Inventory, Discount, Schedule, Category,
  Assessment, LocalOffer, BarChart, PieChart, Timeline
} from '@mui/icons-material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const StatCard = ({ title, value, icon, color = 'primary' }) => (
    <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
        <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: `${color}.main`, mr: 2 }}>{icon}</Avatar>
                <Typography variant="h6" color="text.secondary">{title}</Typography>
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>{value}</Typography>
        </CardContent>
    </Card>
);

function SalesReportsTab() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState({
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });

  const getAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  useEffect(() => {
      fetchReport();
  }, [dateRange]);

  const fetchReport = async () => {
    setLoading(true);
    setError('');
    try {
        const params = new URLSearchParams(dateRange);
        const response = await fetch(`${API_BASE_URL}/api/v1/reports/sales-summary?${params}`, { headers: getAuthHeader() });
        if (!response.ok) throw new Error('Failed to fetch sales summary');
        const data = await response.json();
        setReport(data);
    } catch (err) {
        console.error('Error fetching report:', err);
        setError(err.message || 'Failed to fetch report');
    } finally {
        setLoading(false);
    }
  };

  return (
    <Box>
      <Paper elevation={2} sx={{ p: 2, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Select Date Range</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={5}><TextField label="Start Date" type="date" fullWidth value={dateRange.start_date} onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })} InputLabelProps={{ shrink: true }}/></Grid>
          <Grid item xs={12} sm={5}><TextField label="End Date" type="date" fullWidth value={dateRange.end_date} onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })} InputLabelProps={{ shrink: true }}/></Grid>
          <Grid item xs={12} sm={2}><Button variant="contained" onClick={fetchReport} fullWidth>Generate</Button></Grid>
        </Grid>
      </Paper>

      {loading && <CircularProgress />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {report && (
          <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}><StatCard title="Total Sales" value={`$${report.total_sales_usd || 0}`} icon={<AttachMoney />} /></Grid>
              <Grid item xs={12} sm={6} md={3}><StatCard title="Total Orders" value={report.total_orders || 0} icon={<TrendingUp />} color="success" /></Grid>
              <Grid item xs={12} sm={6} md={3}><StatCard title="Avg. Order Value" value={`$${report.average_order_value_usd || 0}`} icon={<BarChart />} color="info" /></Grid>
              <Grid item xs={12} sm={6} md={3}><StatCard title="Total Discounts" value={`$${report.total_discounts_usd || 0}`} icon={<Discount />} color="warning" /></Grid>

              <Grid item xs={12} md={6}>
                  <Paper elevation={2} sx={{p: 2, borderRadius: 2}}>
                      <Typography variant="h6" sx={{mb: 2}}>Top Selling Items</Typography>
                      <TableContainer>
                          <Table size="small">
                              <TableHead><TableRow><TableCell>Item</TableCell><TableCell align="right">Quantity</TableCell><TableCell align="right">Revenue</TableCell></TableRow></TableHead>
                              <TableBody>
                                  {report.top_selling_items && report.top_selling_items.length > 0 ? (
                                      report.top_selling_items.map(item => (
                                          <TableRow key={item.item_name}><TableCell>{item.item_name}</TableCell><TableCell align="right">{item.total_quantity}</TableCell><TableCell align="right">${item.total_revenue_usd}</TableCell></TableRow>
                                      ))
                                  ) : (
                                      <TableRow><TableCell colSpan={3} align="center">No data available</TableCell></TableRow>
                                  )}
                              </TableBody>
                          </Table>
                      </TableContainer>
                  </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                  <Paper elevation={2} sx={{p: 2, borderRadius: 2}}>
                      <Typography variant="h6" sx={{mb: 2}}>Sales by Category</Typography>
                      <TableContainer>
                          <Table size="small">
                              <TableHead><TableRow><TableCell>Category</TableCell><TableCell align="right">Revenue</TableCell></TableRow></TableHead>
                              <TableBody>
                                  {report.sales_by_category && report.sales_by_category.length > 0 ? (
                                      report.sales_by_category.map(cat => (
                                          <TableRow key={cat.category_name}><TableCell>{cat.category_name}</TableCell><TableCell align="right">${cat.total_revenue_usd}</TableCell></TableRow>
                                      ))
                                  ) : (
                                      <TableRow><TableCell colSpan={2} align="center">No data available</TableCell></TableRow>
                                  )}
                              </TableBody>
                          </Table>
                      </TableContainer>
                  </Paper>
              </Grid>
          </Grid>
      )}
    </Box>
  );
}


export default function ReportsManager() {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      <Tabs value={tab} onChange={(e, val) => setTab(val)} indicatorColor="primary" textColor="primary" sx={{ mb: 3 }}>
        <Tab label="Sales Analytics" icon={<Assessment />} iconPosition="start" />
        {/* Placeholder for future tabs */}
      </Tabs>
      {tab === 0 && <SalesReportsTab />}
    </Box>
  );
} 
