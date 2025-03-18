import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import EmojiPicker, { EmojiClickData } from 'emoji-picker-react';
import { FiSmile, FiPaperclip, FiSend } from 'react-icons/fi';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onFileUpload: (file: File) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onFileUpload }) => {
  const [message, setMessage] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleEmojiClick = (emojiData: EmojiClickData) => {
    setMessage(prev => prev + emojiData.emoji);
    setShowEmojiPicker(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
    }
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="border-t border-gray-200 bg-white p-4"
    >
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setShowEmojiPicker(!showEmojiPicker)}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <FiSmile size={20} />
          </button>
          
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <FiPaperclip size={20} />
          </button>
          
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:outline-none focus:border-blue-500"
          />
          
          <motion.button
            type="submit"
            whileTap={{ scale: 0.95 }}
            className="bg-blue-500 text-white rounded-full p-2 hover:bg-blue-600 focus:outline-none"
          >
            <FiSend size={20} />
          </motion.button>
        </div>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt"
        />

        {showEmojiPicker && (
          <div className="absolute bottom-full right-0 mb-2">
            <EmojiPicker onEmojiClick={handleEmojiClick} />
          </div>
        )}
      </form>
    </motion.div>
  );
};

export default ChatInput;
