import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Team from './pages/Team';
import Account from './pages/Account';
import Sidebar from './components/Sidebar';

// Create a layout component directly in App.tsx since MainLayout is not available
const AppLayout = () => {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 p-6 overflow-y-auto">
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="team" element={<Team />} />
          <Route path="account" element={<Account />} />
        </Routes>
      </main>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;