/**
 * MathTrainer Admin - SVG Animations & Empty States
 */

window.svgAnim = {
    /** 
     * Animated Logo: subtle pulse + drawing effect on load
     */
    logo: (size = 32) => `
        <svg width="${size}" height="${size}" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="logoG1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#8b5cf6" />
                    <stop offset="100%" stop-color="#6366f1" />
                </linearGradient>
                <linearGradient id="logoG2" x1="100%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#a855f7" stop-opacity="0.8" />
                    <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.2" />
                </linearGradient>
                <filter id="logoGlow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            <g style="animation: logoFloat 4s ease-in-out infinite;">
                <!-- Glowing Core -->
                <circle cx="16" cy="16" r="8" fill="url(#logoG1)" filter="url(#logoGlow)" style="animation: logoPulse 2s ease-in-out infinite alternate; opacity: 0.6;" />
                
                <!-- Hexagon Base -->
                <path d="M16 2L28 9V23L16 30L4 23V9L16 2Z" stroke="url(#logoG1)" stroke-width="2" stroke-linejoin="round" fill="url(#logoG2)"
                    style="stroke-dasharray: 100; stroke-dashoffset: 100; animation: logoDraw 1.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;" />
                
                <!-- Math/Infinity Nodes intersecting -->
                <path d="M16 2L16 16L28 23" stroke="url(#logoG1)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                    style="stroke-dasharray: 40; stroke-dashoffset: 40; animation: logoDraw 1s ease 0.6s forwards;" />
                <path d="M4 23L16 16L4 9" stroke="url(#logoG1)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                    style="stroke-dasharray: 40; stroke-dashoffset: 40; animation: logoDraw 1s ease 0.8s forwards;" />
                
                <!-- Center Node -->
                <circle cx="16" cy="16" r="3" fill="#ffffff" style="opacity:0; animation: logoFadeIn 0.8s ease 1.2s forwards;" />
            </g>
        </svg>
        <style>
            @keyframes logoDraw { to { stroke-dashoffset: 0; } }
            @keyframes logoFadeIn { to { opacity: 1; filter: drop-shadow(0 0 5px rgba(255,255,255,0.8)); } }
            @keyframes logoFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }
            @keyframes logoPulse { 0% { opacity: 0.4; transform: scale(0.9); transform-origin: center; } 100% { opacity: 0.8; transform: scale(1.1); transform-origin: center; } }
        </style>
    `,

    /**
     * Elegant Spinner Loader
     */
    loader: (size = 50) => `
        <svg width="${size}" height="${size}" viewBox="0 0 50 50" fill="none" stroke="currentColor">
            <circle cx="25" cy="25" r="20" stroke="rgba(255,255,255,0.1)" stroke-width="4" />
            <circle cx="25" cy="25" r="20" stroke="url(#loader-gradient)" stroke-width="4" stroke-linecap="round" stroke-dasharray="100" stroke-dashoffset="50">
                <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="1s" repeatCount="indefinite" />
            </circle>
            <defs>
                <linearGradient id="loader-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#6366f1" />
                    <stop offset="100%" stop-color="#8b5cf6" />
                </linearGradient>
            </defs>
        </svg>
    `,

    /**
     * Reusable Empty State UI 
     */
    emptyState: (message = "Нет данных") => `
        <div class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--c-text-muted)" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="9" y1="9" x2="15" y2="15" stroke-dasharray="10" stroke-dashoffset="10">
                    <animate attributeName="stroke-dashoffset" values="10;0" dur="0.8s" fill="freeze" />
                </line>
                <line x1="15" y1="9" x2="9" y2="15" stroke-dasharray="10" stroke-dashoffset="10">
                    <animate attributeName="stroke-dashoffset" values="10;0" dur="0.8s" begin="0.2s" fill="freeze" />
                </line>
            </svg>
            <p>${message}</p>
        </div>
    `
};
