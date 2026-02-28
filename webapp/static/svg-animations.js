/**
 * MathTrainer Admin - SVG Animations & Empty States
 */

window.svgAnim = {
    /** 
     * Animated Logo: subtle pulse + drawing effect on load
     */
    logo: (size = 32) => `
        <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="url(#logo-gradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: logo-pulse 3s infinite ease-in-out;">
            <defs>
                <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#6366f1" />
                    <stop offset="100%" stop-color="#8b5cf6" />
                </linearGradient>
            </defs>
            <rect x="4" y="2" width="16" height="20" rx="2" ry="2" stroke-dasharray="80" stroke-dashoffset="80">
                <animate attributeName="stroke-dashoffset" values="80;0" dur="1s" fill="freeze" />
            </rect>
            <line x1="8" y1="6" x2="16" y2="6" stroke-dasharray="8" stroke-dashoffset="8">
                <animate attributeName="stroke-dashoffset" values="8;0" dur="0.5s" begin="0.5s" fill="freeze" />
            </line>
            <circle cx="9" cy="14" r="1.5" fill="var(--c-accent)" />
            <circle cx="15" cy="14" r="1.5" fill="var(--c-accent)" />
            <circle cx="12" cy="17" r="1.5" fill="var(--c-accent-2)" />
            <style>
                @keyframes logo-pulse {
                    0% { filter: drop-shadow(0 0 2px rgba(99, 102, 241, 0.2)); transform: scale(1); }
                    50% { filter: drop-shadow(0 0 8px rgba(139, 92, 246, 0.6)); transform: scale(1.05); }
                    100% { filter: drop-shadow(0 0 2px rgba(99, 102, 241, 0.2)); transform: scale(1); }
                }
            </style>
        </svg>
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
