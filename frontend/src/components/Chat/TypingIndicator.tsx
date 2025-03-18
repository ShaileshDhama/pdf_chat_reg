import React from 'react';
import { motion } from 'framer-motion';

const TypingIndicator: React.FC = () => {
  const dotVariants = {
    initial: { y: 0 },
    animate: { y: -5 },
  };

  const containerVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      className="flex items-center gap-1 text-gray-500 text-sm"
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      <span>AI is typing</span>
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-1.5 h-1.5 bg-gray-500 rounded-full"
            variants={dotVariants}
            animate="animate"
            transition={{
              repeat: Infinity,
              repeatType: "reverse",
              duration: 0.4,
              delay: i * 0.1,
            }}
          />
        ))}
      </div>
    </motion.div>
  );
};

export default TypingIndicator;
