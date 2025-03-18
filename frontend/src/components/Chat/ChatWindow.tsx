import React, { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatBubble from './ChatBubble';
import ChatInput from './ChatInput';

interface Message {
  id: string;
  content: string;
  timestamp: Date;
  isUser: boolean;
  username: string;
  avatar?: string;
}

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onFileUpload: (file: File) => void;
  isTyping: boolean;
  userAvatar?: string;
  botAvatar?: string;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  onSendMessage,
  onFileUpload,
  isTyping,
  userAvatar,
  botAvatar,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm p-4 flex items-center">
        <div className="relative">
          <img
            src={botAvatar || '/bot-avatar.png'}
            alt="Bot"
            className="w-10 h-10 rounded-full"
          />
          <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
        </div>
        <div className="ml-3">
          <h3 className="font-semibold text-gray-800">AI Assistant</h3>
          <p className="text-sm text-gray-500">Online</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <ChatBubble
              key={message.id}
              message={message.content}
              isUser={message.isUser}
              timestamp={message.timestamp}
              avatar={message.isUser ? userAvatar : botAvatar}
            />
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="flex items-center space-x-2 mt-2"
            >
              <div className="flex space-x-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-2 h-2 bg-gray-400 rounded-full"
                    animate={{
                      y: ["0%", "-50%", "0%"],
                    }}
                    transition={{
                      duration: 0.5,
                      repeat: Infinity,
                      delay: i * 0.15,
                    }}
                  />
                ))}
              </div>
              <span className="text-sm text-gray-500">AI is typing...</span>
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSendMessage={onSendMessage} onFileUpload={onFileUpload} />
    </div>
  );
};

export default ChatWindow;
