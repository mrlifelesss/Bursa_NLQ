import React from 'react';

interface SpinnerProps {
    t: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ t }) => (
  <div className="flex flex-col items-center justify-center">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
    <p className="mt-4 text-cyan-400">{t}</p>
  </div>
);