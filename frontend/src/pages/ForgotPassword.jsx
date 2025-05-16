import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import axios from "axios";

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
      email: '',
      password: '',
    });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    try {
        const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/user/forget`, formData);
        console.log(response?.data?.detail)
  
        toast.success(response?.data?.detail);
        setTimeout(() => {
            navigate("/login");
          }, 2000);
      } catch (err) {
        toast.error(err.response?.data?.detail || "Login failed. Please try again.");
      }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-gray-800 rounded-lg p-8 shadow-md">
        <h2 className="text-2xl font-bold text-white mb-6">Reset Password</h2>
        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 rounded p-3 mb-4">
            {error}
          </div>
        )}
        {message && (
          <div className="bg-green-500/10 border border-green-500 text-green-500 rounded p-3 mb-4">
            {message}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-gray-300 block mb-1">Email Address</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="text-gray-300 block mb-1">New Password</label>
            <input
              type="new_password"
              value={formData.new_password}
              onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 transition-colors"
          >
            Reset Password
          </button>
          <p className="text-gray-400 text-center">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-blue-400 hover:underline"
            >
              Back to Login
            </button>
          </p>
        </form>
      </div>
    </div>
  );
};
  
  export default ForgotPassword;
  