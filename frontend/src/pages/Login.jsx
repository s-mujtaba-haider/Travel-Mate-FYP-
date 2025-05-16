import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import axios from "axios";

const Login = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
        const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/user/login`, formData);
        let userData = response?.data?.data
  
        // Save user data to Zustand store
        login({ ...userData, guest: false });
  
        toast.success(response?.data?.detail);
        setTimeout(() => {
            navigate("/chat");
          }, 2000);
      } catch (err) {
        toast.error(err.response?.data?.detail || "Login failed. Please try again.");
      }
  };

  return (

    <>
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-gray-800 rounded-lg p-8 shadow-md">
        <h2 className="text-2xl font-bold text-white mb-6">Login</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-gray-300 block mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-gray-300 block mb-1">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 transition-colors"
          >
            Login
          </button>
        </form>
        <button
            className="w-full mt-4 bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 transition-colors"
            onClick={()=> (navigate("/register"))}
          >
            Register
          </button>
      </div>
    </div>

    </>
  );
};

export default Login;       