import React from 'react';
import {Bot} from 'lucide-react';

const ThinkingAnimation = () => (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
        <Bot className="w-5 h-5 text-white" />
      </div>
      <div className="bg-gray-700 text-gray-100 rounded-lg p-3">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );

export default ThinkingAnimation;