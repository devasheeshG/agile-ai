import React from 'react';
import { Navigate } from 'react-router-dom';

const Signup: React.FC = () => {
  // Simply redirect to the dashboard
  return <Navigate to="/" replace />;
};

export default Signup;