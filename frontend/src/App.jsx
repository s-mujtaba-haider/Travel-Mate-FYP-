import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import UpdateProfile from './pages/UpdateProfile';
import GuestLogin from './pages/GuestLogin';
import Chat from './pages/Chat';
import { useAuthStore } from './store/authStore';
import { ToastContainer } from "react-toastify";

const App = () => {
  const user = useAuthStore((state) => state.user);

  return (
    <>
      <ToastContainer position="top-right" autoClose={1000} hideProgressBar={true} toastClassName="custom-toast" className="custom-toast-container"/>
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={user ? <Navigate to="/chat" /> : <Login />} 
        />
        <Route 
          path="/register" 
          element={user ? <Navigate to="/chat" /> : <Register />} 
        />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/update-profile" element={<UpdateProfile />} />
        <Route 
          path="/guest" 
          element={user ? <Navigate to="/chat" /> : <GuestLogin />} 
        />
        <Route 
          path="/chat" 
          element={user ? <Chat /> : <Navigate to="/guest" />} 
        />
        <Route path="/" element={<Navigate to="/guest" />} />
      </Routes>
    </Router>
    </>
  );
};

export default App;