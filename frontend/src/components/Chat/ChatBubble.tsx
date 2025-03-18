import React from 'react';
import { motion } from 'framer-motion';

interface ChatBubbleProps {
  message: string;
  isUser: boolean;
  timestamp: Date;
  avatar?: string;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ message, isUser, timestamp, avatar }) => {
  const bubbleVariants = {
    initial: {
      opacity: 0,
      scale: 0.8,
      x: isUser ? 20 : -20,
    },
    animate: {
      opacity: 1,
      scale: 1,
      x: 0,
      transition: {
        type: "spring",
        stiffness: 500,
        damping: 30,
      },
    },
  };

  return (
    <motion.div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      initial="initial"
      animate="animate"
      variants={bubbleVariants}
    >
      {!isUser && (
        <div className="flex-shrink-0 mr-3">
          <img
            className="h-8 w-8 rounded-full"
            src={avatar || '/bot-avatar.png'}
            alt="Bot Avatar"
          />
        </div>
      )}
      <div
        className={`relative max-w-xl px-4 py-2 ${
          isUser
            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-l-lg rounded-br-lg'
            : 'bg-gray-100 text-gray-800 rounded-r-lg rounded-bl-lg'
        } shadow-md`}
      >
        <span className="block">{message}</span>
        <span
          className={`block text-xs ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          } mt-1`}
        >
          {new Date(timestamp).toLocaleTimeString()}
        </span>
      </div>
      {isUser && (
        <div className="flex-shrink-0 ml-3">
          <img
            className="h-8 w-8 rounded-full"
            src={avatar || '/user-avatar.png'}
            alt="User Avatar"
          />
        </div>
      )}
    </motion.div>
  );
};

export default ChatBubble;
