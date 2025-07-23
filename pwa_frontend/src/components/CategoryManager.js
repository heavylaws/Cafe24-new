import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Box, Paper, Typography, Button, TextField, Dialog, DialogTitle,
  DialogContent, DialogActions, Alert, CircularProgress, IconButton,
  Stack, List, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { Add, Edit, Delete, ArrowDropDown, ArrowRight } from '@mui/icons-material';

const API_URL = `${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/v1/categories`;

// Helper function to flatten the category tree for the parent selector
const flattenCategories = (categories, parentName = '', level = 0) => {
  let flatList = [];
  categories.forEach(category => {
    const newName = parentName ? `${parentName} > ${category.name}` : category.name;
    flatList.push({ ...category, displayName: newName, level });
    if (category.children && category.children.length > 0) {
      flatList = flatList.concat(flattenCategories(category.children, newName, level + 1));
    }
  });
  return flatList;
};

// Recursive component to render the category tree
function CategoryTreeItem({ category, onEdit, onDelete, onAddChild }) {
  const [isOpen, setIsOpen] = useState(true); // Default to open

  return (
    <Box sx={{ pl: category.parent_id ? 2 : 0 }}>
      <Paper elevation={1} sx={{ mb: 1, borderRadius: 1 }}>
        <Stack direction="row" alignItems="center" sx={{ p: 1 }}>
          <IconButton size="small" onClick={() => setIsOpen(!isOpen)} disabled={!category.children || category.children.length === 0}>
            {category.children && category.children.length > 0 ? (isOpen ? <ArrowDropDown /> : <ArrowRight />) : <span style={{ width: 20 }} />}
          </IconButton>
          <Typography variant="body1" sx={{ flexGrow: 1, fontWeight: 500 }}>
            {category.name}
          </Typography>
          <Button size="small" startIcon={<Add />} onClick={() => onAddChild(category)} sx={{ mr: 1 }}>
            Add Sub
          </Button>
          <Button size="small" variant="outlined" startIcon={<Edit />} onClick={() => onEdit(category)}>
            Edit
          </Button>
          <IconButton color="error" size="small" onClick={() => onDelete(category.id)}>
            <Delete />
          </IconButton>
        </Stack>
      </Paper>
      {isOpen && category.children && (
        <List component="div" disablePadding>
          {category.children.map(child => (
            <CategoryTreeItem key={child.id} category={child} onEdit={onEdit} onDelete={onDelete} onAddChild={onAddChild} />
          ))}
        </List>
      )}
    </Box>
  );
}

function CategoryManager() {
  const [categories, setCategories] = useState([]);
  const [flatCategories, setFlatCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState('');

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [categoryName, setCategoryName] = useState('');
  const [sortOrder, setSortOrder] = useState(0);
  const [parentId, setParentId] = useState(null);

  const getAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(API_URL, { headers: getAuthHeader() });
      setCategories(res.data);
      setFlatCategories(flattenCategories(res.data));
    } catch (err) {
      setError('Failed to fetch categories.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const handleOpenDialog = (category = null, isSubcategory = false) => {
    setEditingCategory(category && !isSubcategory ? category : null);
    setCategoryName(category && !isSubcategory ? category.name : '');
    setSortOrder(category && !isSubcategory ? category.sort_order : 0);
    setParentId(isSubcategory ? category.id : (category ? category.parent_id : null));
    setError(null);
    setSuccess('');
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  const handleSubmit = async () => {
    const url = editingCategory ? `${API_URL}/${editingCategory.id}` : API_URL;
    const method = editingCategory ? 'put' : 'post';
    const data = {
      name: categoryName,
      sort_order: Number(sortOrder) || 0,
      parent_id: parentId === 'null' ? null : parentId,
    };

    try {
      await axios[method](url, data, { headers: getAuthHeader() });
      setSuccess(`Category successfully ${editingCategory ? 'updated' : 'created'}!`);
      handleCloseDialog();
      fetchCategories();
    } catch (err) {
      setError(err.response?.data?.message || 'An error occurred.');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await axios.delete(`${API_URL}/${id}`, { headers: getAuthHeader() });
        setSuccess('Category deleted successfully!');
        fetchCategories();
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to delete category.');
      }
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>Manage Categories</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          Add Root Category
        </Button>
      </Box>

      {loading && <CircularProgress />}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {!loading && categories.length > 0 && (
        <List>
          {categories.map((category) => (
            <CategoryTreeItem
              key={category.id}
              category={category}
              onEdit={handleOpenDialog}
              onDelete={handleDelete}
              onAddChild={(parent) => handleOpenDialog(parent, true)}
            />
          ))}
        </List>
      )}

      {!loading && categories.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 4 }}>
          <Typography variant="h6" color="text.secondary">No Categories Found</Typography>
          <Typography color="text.secondary">Click "Add Root Category" to create your first one.</Typography>
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} fullWidth maxWidth="sm">
        <DialogTitle>{editingCategory ? 'Edit Category' : 'Add New Category'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus margin="dense" label="Category Name" type="text" fullWidth
            variant="outlined" value={categoryName} onChange={(e) => setCategoryName(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="parent-category-select-label">Parent Category (Optional)</InputLabel>
            <Select
              labelId="parent-category-select-label"
              value={parentId || 'null'}
              label="Parent Category (Optional)"
              onChange={(e) => setParentId(e.target.value === 'null' ? null : e.target.value)}
            >
              <MenuItem value="null"><em>None (Root Category)</em></MenuItem>
              {flatCategories.map((cat) => (
                <MenuItem
                  key={cat.id}
                  value={cat.id}
                  disabled={editingCategory && (cat.id === editingCategory.id || (cat.displayName && editingCategory.name && cat.displayName.startsWith(editingCategory.name)))}
                  sx={{ pl: `${cat.level * 1.5 + 1}rem` }}
                >
                  {cat.displayName}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense" label="Sort Order" type="number" fullWidth
            variant="outlined" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}
            helperText="Lower numbers appear first on the menu."
          />
        </DialogContent>
        <DialogActions sx={{ p: '16px 24px' }}>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingCategory ? 'Save Changes' : 'Create Category'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default CategoryManager;
