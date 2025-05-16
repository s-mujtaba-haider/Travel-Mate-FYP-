import React, { useState, useEffect, useRef } from 'react';
import { User, Bot, Menu, X, Settings, LogOut } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import InputField from './InputField';
import ChatSidebar from './ChatSidebar';
import LocationCard from './LocationCard';
import ThinkingAnimation from './ThinkingAnimation';

const ChatWindow = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [sessionName, setSessionName] = useState('New Chat');
  const [isFirstMessage, setIsFirstMessage] = useState(true);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: user?.guest
        ? "Welcome to Travel Mate! I'm here to help plan your perfect trip in Pakistan. Note that this is a guest session and your chat history won't be saved."
        : `Welcome ${user?.first_name} to Travel Mate! How can I assist with your travel plans today?`,
    },
  ]);

  const messagesContainerRef = useRef(null);
  const profileMenuRef = useRef(null);
  const sidebarRef = useRef(null);

  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/session/create`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${user?.token}`,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        });

        if (!response.ok) throw new Error(`Failed to create session: ${response.statusText}`);

        const data = await response.json();
        setSelectedSessionId(data.session_id);
        setSessions((prev) => [{ id: data.session_id, name: 'New Chat' }, ...prev]); // Add to sidebar
      } catch (error) {
        console.error("Error creating session:", error);
      }
    };

    if (user?.token) createSession();
  }, [user?.token]);

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Close profile menu and sidebar when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setIsProfileMenuOpen(false);
      }
      
      if (sidebarRef.current && 
          !sidebarRef.current.contains(event.target) && 
          !event.target.closest('[data-menu-button]')) {
        setIsMobileSidebarOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/guest');
    setIsProfileMenuOpen(false);
  };

  const handleUpdateProfile = () => {
    navigate('/update-profile');
    setIsProfileMenuOpen(false);
  };

  const toggleProfileMenu = () => {
    setIsProfileMenuOpen(!isProfileMenuOpen);
  };

  const toggleMobileSidebar = () => {
    setIsMobileSidebarOpen(!isMobileSidebarOpen);
  };

  const handleSendMessage = async (content) => {
    if (!user?.token) {
      console.error("No authentication token available.");
      return;
    }

    const newMessage = { role: 'human', content };
    setMessages((prev) => [...prev, newMessage]);
    setIsLoading(true);

    try {
      if (isFirstMessage) {
        const sessionName = content.split(" ").slice(0, 5).join(" "); // Use first 5 words
        setSessionName(sessionName); // Update state

        const updateSessionResponse = await fetch(
          `${process.env.REACT_APP_BACKEND_URL}/session/update/${selectedSessionId}?session_name=${encodeURIComponent(sessionName)}`,
          {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${user?.token}`,
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
          }
        );

        if (!updateSessionResponse.ok) {
          throw new Error(`Session update failed: ${updateSessionResponse.statusText}`);
        }

        // Update session name in sidebar
        setSessions((prev) =>
          prev.map((session) =>
            session.id === selectedSessionId ? { ...session, name: sessionName } : session
          )
        );

        setIsFirstMessage(false); // Mark session update as done
      }
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/chat/query/${selectedSessionId}?query=${encodeURIComponent(content)}&max_places=5`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${user?.token}`,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        }
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();

      const { message, places } = data.content;

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: message },
        ...(places?.length
          ? places.map((place) => ({
              role: 'assistant',
              content: <LocationCard key={place.place_id} place={place} />
            }))
          : []),
      ]);
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages((prev) => [...prev, { role: 'assistant', content: "An error occurred. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-gray-900 text-white flex-col">
      {/* Main Header */}
      <header className="bg-gray-800 border-b border-gray-700 py-4 px-6">
        <div className="flex items-center justify-between max-w-[1920px] mx-auto">
          <div className="flex items-center space-x-2">
          <button 
              data-menu-button
              onClick={toggleMobileSidebar} 
              className="md:hidden flex items-center justify-center"
            >
              {isMobileSidebarOpen ? (
                <X className="w-6 h-6 text-gray-400" />
              ) : (
                <Menu className="w-6 h-6 text-gray-400" />
              )}
            </button>
            <h1 className="text-xl font-bold text-white">Travel Mate</h1>
          </div>
          
          {/* Profile Button with Dropdown */}
          <div className="relative" ref={profileMenuRef}>
            <button
              onClick={toggleProfileMenu}
              className="flex items-center space-x-2 bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
            >
              <User className="w-5 h-5" />
              <span>Profile</span>
            </button>
            
            {isProfileMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-md shadow-lg overflow-hidden z-10">
                {!user?.guest && (
                  <button
                    onClick={handleUpdateProfile}
                    className="flex items-center w-full px-4 py-3 text-sm text-left text-white hover:bg-gray-700 transition-colors"
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Update Profile
                  </button>
                )}
                <button
                  onClick={handleLogout}
                  className="flex items-center w-full px-4 py-3 text-sm text-left text-white hover:bg-gray-700 transition-colors"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  {user?.guest ? 'Exit Guest Session' : 'Logout'}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Guest Session Banner */}
      {user?.guest && (
        <div className="bg-blue-600 text-white text-center py-2 px-4">
          Guest Session - <a href="/login" className="underline">Login</a> to save your chat history
        </div>
      )}

<div className="flex flex-1 overflow-hidden relative">
        {/* Mobile sidebar overlay - add this for backdrop */}
        {isMobileSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden" 
            onClick={() => setIsMobileSidebarOpen(false)}
          > </div>
        )}
        
        {/* Only show sidebar for logged-in users */}
        {user && !user.guest && (
          <div 
            ref={sidebarRef}
            className={`fixed md:relative left-0 top-[81px] md:top-0 h-[calc(100%-81px)] md:h-full bg-gray-900 z-40 transition-transform duration-300 ease-in-out ${
              isMobileSidebarOpen ? 'translate-x-0 w-[300px]' : '-translate-x-full md:translate-x-0 w-96'
            } shadow-lg md:shadow-none`}
          >
            <ChatSidebar 
              sessions={sessions} 
              onSelectSession={(sessionId, history) => {
                setSelectedSessionId(sessionId);
                setIsMobileSidebarOpen(false);
              }} 
            />
          </div>
        )}
        <div className="flex-1 flex flex-col items-center justify-between p-6 max-w-4xl mx-auto w-full">
          <div 
            ref={messagesContainerRef}
            className="flex-1 w-full overflow-y-auto p-4 bg-gray-800 rounded-lg shadow-md scrollbar-hide"
            style={{
              scrollbarWidth: 'none', /* Firefox */
              msOverflowStyle: 'none', /* IE and Edge */
            }}
          >
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex items-start gap-3 ${
                    message.role === 'human' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'human'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-100'
                    }`}
                  >
                    {typeof message.content === 'string' ? (
                      <p className="text-sm">{message.content}</p>
                    ) : (
                      message.content
                    )}
                  </div>
                  {message.role === 'human' && (
                    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                      <User className="w-5 h-5 text-white" />
                    </div>
                  )}
                </div>
              ))}
              {isLoading && <ThinkingAnimation />}
            </div>
          </div>

          <div className="w-full mt-4 relative">
            <InputField onSendMessage={handleSendMessage} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;