import React, { useState } from 'react';
import Login from './Login';
import DashboardManager from './DashboardManager';
import DashboardCourier from './DashboardCourier';
import DashboardBarista from './DashboardBarista';
import DashboardCashier from './DashboardCashier';

function App() {
  const [user, setUser] = useState(null);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  // Handle both uppercase (from backend) and lowercase role formats
  const userRole = user.role.toLowerCase();
  
  switch (userRole) {
    case 'manager':
      return <DashboardManager user={user} onLogout={handleLogout} />;
    case 'courier':
      return <DashboardCourier user={user} onLogout={handleLogout} />;
    case 'barista':
      return <DashboardBarista user={user} onLogout={handleLogout} />;
    case 'cashier':
      return <DashboardCashier user={user} onLogout={handleLogout} />;
    default:
      return (
        <div style={{ textAlign: 'center', marginTop: '3rem' }}>
          <h2>Unknown Role: {user.role}</h2>
          <p>Debug info: Role received = "{user.role}"</p>
          <button onClick={handleLogout}>Logout</button>
        </div>
      );
  }
}

export default App;
