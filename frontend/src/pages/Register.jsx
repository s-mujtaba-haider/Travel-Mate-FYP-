import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import axios from "axios";


const Register = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    dob: '',
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const BASE_URL = process.env.REACT_APP_BACKEND_URL;
  console.log("BASE", BASE_URL)

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    for (const key in formData) {
        if (!formData[key].trim()) {
          setError(`Please fill in all fields.`);
          return;
        }
      }

      try {
        const  data  = await axios.post(`${BASE_URL}/user/signup`, formData);
        console.log(data);
        toast.success(data?.data?.detail);
        setTimeout(() => {
          navigate("/login");
        }, 2000);
      } catch (err) {
        toast.error(err.response?.data?.detail[0]?.msg || err.response?.data?.detail  || "Registration failed. Please try again.");
      }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-gray-800 rounded-lg p-8 shadow-md">
        <h2 className="text-2xl font-bold text-white mb-6">Create Account</h2>
        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 rounded p-3 mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-gray-300 block mb-1">First Name</label>
            <input
              type="first_name"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="text-gray-300 block mb-1">Last Name</label>
            <input
              type="last_name"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="text-gray-300 block mb-1">Date of Birth</label>
            <input
              type="dob"
              placeholder='2000-12-31'
              value={formData.dob}
              onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="text-gray-300 block mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="text-gray-300 block mb-1">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 transition-colors"
          >
            Register
          </button>
          <p className="text-gray-400 text-center">
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-blue-400 hover:underline"
            >
              Login
            </button>
          </p>
        </form>
      </div>
    </div>
  );
};
  
  export default Register;
  