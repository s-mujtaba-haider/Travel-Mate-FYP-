import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import axios from "axios";

const GuestLogin = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const startGuestChat =async () => {
    try {
        const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/user/guest`);
        let userData = response?.data?.data
  
        // Save user data to Zustand store
        login({ ...userData, guest: true });
  
        toast.success(response?.data?.detail);
        setTimeout(() => {
            navigate("/chat");
          }, 2000);
      } catch (err) {
        toast.error(err.response?.data?.detail || "Login failed. Please try again.");
      }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-gray-800 rounded-lg p-8 shadow-md text-center">
        <h2 className="text-2xl font-bold text-white mb-6">Welcome to Travel Mate</h2>
        <div className="space-y-4">
          <button
            onClick={startGuestChat}
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 transition-colors"
          >
            Continue as Guest
          </button>
          <div className="text-gray-400">or</div>
          <button
            onClick={() => navigate('/login')}
            className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 hover:bg-gray-600 transition-colors"
          >
            Login to Your Account
          </button>
        </div>
      </div>
    </div>
  );
};

export default GuestLogin;