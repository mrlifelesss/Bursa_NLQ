import React, { useEffect } from 'react';
import { CloseIcon } from './Icons';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  size?: 'md' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, children, size = 'md' }) => {
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, [onClose]);

  if (!isOpen) {
    return null;
  }

  const sizeClasses = {
    md: 'max-w-md',
    xl: 'max-w-4xl',
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className={`bg-gray-800 rounded-lg shadow-xl border border-gray-700 w-full m-4 flex flex-col ${sizeClasses[size]}`}
        onClick={(e) => e.stopPropagation()} // Prevent closing modal when clicking inside
        style={{ maxHeight: '90vh' }}
      >
        <div className="flex justify-between items-center border-b border-gray-700 p-4 flex-shrink-0">
           <div id="modal-title" className="text-lg font-medium text-white">
             {/* Title can be passed as a prop or defined inside children */}
           </div>
           <button onClick={onClose} className="text-gray-400 hover:text-white">
              <CloseIcon className="h-6 w-6" />
           </button>
        </div>
        <div className="p-6 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};