import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAuthStore } from "../store/authStore";
import { Pencil, Trash2  } from "lucide-react";
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const ChatSidebar = ({ onSelectSession }) => {
  const user = useAuthStore((state) => state.user);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [hoveredSession, setHoveredSession] = useState(null);

  const token = user?.token;

  useEffect(() => {
    if (!token) return;

    const fetchSessions = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/session/all`, {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        });

        const normalizedSessions = response?.data?.data?.sessions.map((session) => ({
          ...session,
          session_id: session?.id || session?.session_id,
        }));

        setSessions(normalizedSessions);
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to fetch sessions");
        setLoading(false);
      }
    };

    fetchSessions();
  }, [token]);

  const handleNewChat = async () => {
    if (!token) return;

    try {
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/session/create`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );

      const newSession = {
        ...response?.data?.data,
        session_id: response?.data?.data?.session_id, 
      };

      setSessions((prevSessions) => [newSession, ...prevSessions]);
      setSelectedSession(newSession?.session_id);
      onSelectSession(newSession?.session_id);
    } catch (err) {
      console.error("Error creating chat:", err.response?.data?.detail || err.message);
    }
  };

  const handleSelectSession = async (sessionId) => {
    setSelectedSession(sessionId);
  
    if (!token) return;
  
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/chat/history/${sessionId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );
  
      const chatHistory = response?.data?.history || [];
  
      onSelectSession(sessionId, chatHistory);
    } catch (err) {
      console.error("Error fetching chat history:", err.response?.data?.detail || err.message);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!token) return;

    try {
      let response = await axios.delete(`${process.env.REACT_APP_BACKEND_URL}/session/delete/${sessionId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
      });

      // Remove deleted session from the list
      setSessions((prevSessions) => prevSessions.filter((session) => session.session_id !== sessionId));

      if (selectedSession === sessionId) {
        setSelectedSession(null);
        onSelectSession(null);
      }
      toast.success(response?.data?.detail);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Login failed. Please try again.");
      console.error("Error deleting chat:", err.response?.data?.detail || err.message);
    }
  };

  if (!user || user.guest) return null;

  return (
    <div className="h-screen bg-gray-800 p-4 border-r border-gray-700">
      <h2 className="text-gray-400 font-semibold mb-4">Chat History</h2>
      <button
        className="flex items-center w-full bg-blue-600 text-white p-2 rounded mb-4 hover:bg-blue-700"
        onClick={handleNewChat}
      >
        <Pencil size={18} className="mr-2" /> New Chat
      </button>

      {/* Invisible Scrollable Chat List */}
      <div className="space-y-2 h-[calc(100vh-100px)] overflow-y-auto scrollbar-hide"
      style={{
        scrollbarWidth: 'none', /* Firefox */
        msOverflowStyle: 'none', /* IE and Edge */
      }}
      >
      {sessions?.length === 0 ? (
    <p className="text-gray-400 text-center">No chats available</p>
  ) :
  sessions?.map((session, index) => (
          <div
            key={session.session_id}
            className={`flex items-center justify-between p-2 rounded cursor-pointer ${
              selectedSession === session.session_id ? "bg-blue-700 text-white" : "hover:bg-gray-700 text-gray-300"
            }`}
            onMouseEnter={() => setHoveredSession(session.session_id)}
            onMouseLeave={() => setHoveredSession(null)}
            onClick={() => handleSelectSession(session.session_id)}
          >
            <span className="flex-1 truncate">{session?.session_name || `New Chat`}</span>
            {hoveredSession === session.session_id && (
              <Trash2
                size={18}
                className="text-red-400 hover:text-red-600 cursor-pointer ml-2"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteSession(session.session_id);
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatSidebar;
