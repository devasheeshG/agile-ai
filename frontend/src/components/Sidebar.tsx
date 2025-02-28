import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, UserCircle } from 'lucide-react';

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-secondary border-r border-border h-screen flex flex-col">
      <div className="p-4 border-b border-border">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <LayoutDashboard className="text-primary" />
          <span>AgileAi</span>
        </h1>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={20} />
          <span>Dashboard</span>
        </NavLink>
        
        <NavLink to="/team" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Users size={20} />
          <span>Team</span>
        </NavLink>
        
        <NavLink to="/account" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <UserCircle size={20} />
          <span>Account</span>
        </NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;