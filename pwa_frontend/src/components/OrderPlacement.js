import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Grid, Card, CardContent, CardActions, Button, 
  TextField, Select, MenuItem, Chip, Alert, CircularProgress, Dialog, 
  DialogTitle, DialogContent, DialogActions, List, ListItem, ListItemText,
  Divider, IconButton, Badge, Snackbar, FormControl, InputLabel, Avatar,
  CardMedia, Stack, Fade, Zoom
} from '@mui/material';
import { 
  Add, Remove, ShoppingCart, Delete, Discount, LocalOffer, 
  AttachMoney, Category, Restaurant, Star
} from '@mui/icons-material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';


function OrderPlacement({ userRole }) {
  const [menuData, setMenuData] = useState([]);
  const [categories, setCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [cart, setCart] = useState([]);
  const [customerNumber, setCustomerNumber] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [placingOrder, setPlacingOrder] = useState(false);
  const [exchangeRate, setExchangeRate] = useState(1500); // This should also come from API
  const [discounts, setDiscounts] = useState([]);
  const [showDiscountDialog, setShowDiscountDialog] = useState(false);
  const [selectedDiscount, setSelectedDiscount] = useState(null);
  const [discountTarget, setDiscountTarget] = useState(null);
  const [orderDiscounts, setOrderDiscounts] = useState([]);
  const [itemDiscounts, setItemDiscounts] = useState({});


  const getAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  useEffect(() => {
    fetchData();
    // Also fetch available discounts for cashier/manager roles
    if (userRole === 'cashier' || userRole === 'manager') {
      fetchDiscounts();
    }
  }, [userRole]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/menu/active`, {
        headers: getAuthHeader()
      });
      if (!response.ok) throw new Error('Failed to fetch menu data');
      const data = await response.json();
      
      // Handle the correct data structure from backend
      setMenuItems(data.menu_items || []);
      setCategories(data.categories || []);
      
      // Create the structure expected by the component
      const menuDataWithItems = (data.categories || []).map(category => ({
        category_id: category.id,
        category_path: category.path,
        items: (data.menu_items || []).filter(item => item.category_id === category.id)
      }));
      setMenuData(menuDataWithItems);
      
    } catch (err) {
      setError('Failed to fetch menu data');
      console.error('Menu fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDiscounts = async () => {
    // Fetches active discounts
    // ... implementation
  };

  const addToCart = (item, choice = null) => {
    const cartItemId = choice ? `${item.id}-${choice.choice_id}` : item.id;
    const existingItem = cart.find(i => i.cartId === cartItemId);
    
    const price = choice ? parseFloat(choice.price_usd) || 0 : parseFloat(item.base_price_usd) || 0;
    const price_lbp = choice ? parseFloat(choice.price_lbp_rounded) || 0 : parseFloat(item.price_lbp_rounded) || 0;
    const itemName = choice ? `${item.name} (${choice.choice_name})` : item.name;

    if (existingItem) {
      setCart(cart.map(i => i.cartId === cartItemId ? { ...i, quantity: i.quantity + 1 } : i));
    } else {
      setCart([...cart, {
        cartId: cartItemId,
        id: item.id,
        name: itemName,
        quantity: 1, 
        price_usd: price, 
        price_lbp_rounded: price_lbp,
        choice_id: choice ? choice.choice_id : null,
      }]);
    }
    setSuccess(`${itemName} added to cart!`);
  };

  const removeFromCart = (cartId) => {
    setCart(cart.filter(item => item.cartId !== cartId));
    // Also remove any discounts associated with this cart item
  };

  const updateQuantity = (cartId, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(cartId);
      return;
    }
    setCart(cart.map(i => i.cartId === cartId ? { ...i, quantity: newQuantity } : i));
  };
  
  const calculateSubtotal = () => {
    return cart.reduce((total, item) => total + ((parseFloat(item.price_usd) || 0) * item.quantity), 0);
  };
  
  const placeOrder = async () => {
    if (cart.length === 0) {
      setError('Cart is empty.');
      return;
    }
    // Remove customer number requirement
    // if (!customerNumber.trim()) {
    //     setError('Customer number is required.');
    //     return;
    // }

    setPlacingOrder(true);
    setError('');
    setSuccess('');

    const orderPayload = {
      customer_number: customerNumber.trim() || null, // Make it optional
      items: cart.map(item => {
        const menuItemId = parseInt(item.id);
        const quantity = parseInt(item.quantity);
        const choiceId = item.choice_id ? parseInt(item.choice_id) : null;
        
        console.log('Item data:', {
          original: item,
          parsed: { menuItemId, quantity, choiceId },
          types: {
            menuItemId: typeof menuItemId,
            quantity: typeof quantity,
            choiceId: typeof choiceId
          }
        });
        
        return {
          menu_item_id: menuItemId, // Ensure it's an integer
          quantity: quantity, // Ensure it's an integer
          chosen_option_choice_id: choiceId // Ensure it's an integer or null
        };
      }),
      // Future: add discounts payload
    };

    console.log('Sending order payload:', orderPayload); // Add debugging

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/orders`, {
        method: 'POST',
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderPayload)
      });
      if (!res.ok) {
        const errorData = await res.json();
        console.error('Order creation error:', errorData); // Add debugging
        throw new Error(errorData.message || `Failed to place order. Status: ${res.status}`);
      }
      setSuccess('Order placed successfully!');
      setCart([]);
      setCustomerNumber('');
    } catch (err) {
      console.error('Order placement error:', err); // Add debugging
      setError(err.message);
    } finally {
      setPlacingOrder(false);
    }
  };

  const allItems = menuItems;
  
  const filteredItems = selectedCategory
    ? menuItems.filter(item => item.category_id === selectedCategory)
    : allItems;

  if (loading) return <CircularProgress sx={{ display: 'block', margin: 'auto', mt: 4 }} />;

  return (
    <Box sx={{ p: 2 }}>
       {error && <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>{error}</Alert>}
      <Grid container spacing={3}>
        {/* Header removed for brevity, assuming it's in DashboardCourier */}

        {/* Menu Items */}
        <Grid item xs={12} md={7}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 3, minHeight: '70vh' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Restaurant sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                Menu
              </Typography>
            </Box>
            
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Filter by Category</InputLabel>
              <Select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                label="Filter by Category"
                sx={{ borderRadius: 2 }}
              >
                <MenuItem value=""><em>All Categories</em></MenuItem>
                {categories.map(category => (
                  <MenuItem key={category.id} value={category.id}>
                    {category.path}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Grid container spacing={2}>
              {filteredItems.map((item, index) => (
                <Grid xs={12} sm={6} md={4} key={item.id}>
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{item.image_url && `${item.image_url} `}{item.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{item.category_name}</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ minHeight: 40, mt: 1 }}>{item.description}</Typography>
                      {item.options && item.options.length > 0 ? (
                        item.options.map(opt => opt.choices.map(choice => (
                           <Box key={choice.choice_id} sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', my: 1}}>
                              <Typography variant="body1">{choice.choice_name}</Typography>
                              <Button size="small" variant="outlined" onClick={() => addToCart(item, choice)}>
                                ${(parseFloat(choice.price_usd) || 0).toFixed(2)}
                              </Button>
                           </Box>
                        )))
                      ) : (
                        <Typography variant="h5" color="primary.main" sx={{ fontWeight: 'bold', mt: 2 }}>
                          ${(parseFloat(item.base_price_usd) || 0).toFixed(2)}
                        </Typography>
                      )}
                    </CardContent>
                    {(!item.options || item.options.length === 0) && (
                      <CardActions>
                        <Button fullWidth variant="contained" onClick={() => addToCart(item)}>Add to Cart</Button>
                      </CardActions>
                    )}
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Your Order */}
        <Grid item xs={12} md={5}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 3, position: 'sticky', top: '20px' }}>
             <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShoppingCart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>Your Order</Typography>
             </Box>

             <TextField
                label="Customer Phone Number (Optional)"
                value={customerNumber}
                onChange={(e) => setCustomerNumber(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
             />

            {cart.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">Your cart is empty</Typography>
              </Box>
            ) : (
              <List>
                {cart.map(item => (
                  <ListItem key={item.cartId} dense>
                    <ListItemText 
                      primary={item.name} 
                      secondary={`$${(parseFloat(item.price_usd) || 0).toFixed(2)}`}
                    />
                    <Stack direction="row" alignItems="center" spacing={1}>
                       <IconButton size="small" onClick={() => updateQuantity(item.cartId, item.quantity - 1)}><Remove /></IconButton>
                       <Typography>{item.quantity}</Typography>
                       <IconButton size="small" onClick={() => updateQuantity(item.cartId, item.quantity + 1)}><Add /></IconButton>
                       <IconButton edge="end" color="error" size="small" onClick={() => removeFromCart(item.cartId)}><Delete/></IconButton>
                    </Stack>
                  </ListItem>
                ))}
                <Divider sx={{ my: 2 }} />
                <ListItem>
                    <ListItemText primary={<Typography sx={{fontWeight: 'bold'}}>Subtotal</Typography>} />
                    <Typography sx={{fontWeight: 'bold'}}>${calculateSubtotal().toFixed(2)}</Typography>
                </ListItem>
              </List>
            )}

            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={placeOrder}
              disabled={cart.length === 0 || placingOrder}
              sx={{ mt: 2, py: 1.5, borderRadius: 25 }}
            >
              {placingOrder ? <CircularProgress size={24} color="inherit" /> : 'Place Order'}
            </Button>
          </Paper>
        </Grid>
        <Snackbar
            open={!!success}
            autoHideDuration={3000}
            onClose={() => setSuccess('')}
            message={success}
        />
      </Grid>
    </Box>
  );
}

export default OrderPlacement; 
