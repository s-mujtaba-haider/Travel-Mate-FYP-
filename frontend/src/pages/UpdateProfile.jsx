import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { ArrowLeft, Save, User } from 'lucide-react';
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const UpdateProfile = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    dob: ''
  });

  useEffect(() => {
    const fetchUserData = async () => {
      if (!user?.token) {
        navigate('/login');
        return;
      }else {
        setFormData({
          first_name: user?.first_name || '',
          last_name: user?.last_name || '',
          dob: user?.dob || ''
        });
      }
    };
    
    fetchUserData();
  }, [user, navigate]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!user?.token) {
      navigate('/login');
      return;
    }
    
    try {
      setIsLoading(true);
      setMessage({ type: '', text: '' });
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/user/update`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      
      if (!response.ok) {
         toast.error(result?.detail || 'Failed to update profile');
      }
       toast.success('Profile updated successfully!')
      
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error(error.message || 'An error occurred while updating your profile');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-lg mx-auto p-6">
        <div className="mb-6 flex items-center">
          <button 
            onClick={() => navigate('/chat')} 
            className="mr-4 p-2 rounded-full hover:bg-gray-700 transition-colors"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <h1 className="text-2xl font-bold">Update Profile</h1>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="flex justify-center mb-6">
            <div className="w-24 h-24 bg-gray-700 rounded-full flex items-center justify-center">
              <User className="w-12 h-12 text-gray-400" />
            </div>
          </div>
          
          {message.text && (
            <div className={`mb-4 p-3 rounded ${
              message.type === 'success' ? 'bg-green-800 text-green-100' : 'bg-red-800 text-red-100'
            }`}>
              {message.text}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-1">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full bg-gray-700 text-white rounded px-4 py-2 opacity-70 cursor-not-allowed"
                />
                <p className="text-xs text-gray-400 mt-1">Email cannot be changed</p>
              </div>
              
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  id="first_name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="w-full bg-gray-700 text-white rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="w-full bg-gray-700 text-white rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label htmlFor="dob" className="block text-sm font-medium mb-1">
                  Date of Birth
                </label>
                <input
                  type="date"
                  id="dob"
                  name="dob"
                  value={formData.dob}
                  onChange={handleChange}
                  className="w-full bg-gray-700 text-white rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex items-center justify-center bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Updating...
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <Save className="w-5 h-5 mr-2" />
                      Save Changes
                    </span>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UpdateProfile;