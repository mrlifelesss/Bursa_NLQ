import React from 'react';

export const GatedContent: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    // Set a container height to show approx 3 lines + the fade/blur effect
    <div className="relative h-24 overflow-hidden">
        {/* The blurred version of the text sits at the back. It's visible where the top layer becomes transparent. */}
        {/* Increased blur and added opacity to make the obscured text more visible yet clearly gated. */}
        <div className="blur opacity-75">
            {children}
        </div>
        {/* The clear version sits on top, but is masked with a gradient. */}
        {/* This makes the top part clear, and it fades away to reveal the blur underneath. */}
        <div className="absolute inset-0 [mask-image:linear-gradient(to_bottom,black_60%,transparent_100%)]">
            {children}
        </div>
    </div>
);