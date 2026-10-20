/**
 * fail-but-pretty - Main JavaScript
 * Shared utilities and interactions for error pages
 */

(function() {
    'use strict';

    // ==========================================================================
    // Utility Functions
    // ==========================================================================

    const $ = (selector, context = document) => context.querySelector(selector);
    const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

    const random = (min, max) => Math.random() * (max - min) + min;
    const randomInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));
    const lerp = (a, b, t) => a + (b - a) * t;

    // ==========================================================================
    // Reduced Motion Check
    // ==========================================================================

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ==========================================================================
    // Go Back Button Enhancement
    // ==========================================================================

    function enhanceGoBackButton() {
        const btn = $('#goBackBtn');
        if (!btn) return;

        // Add keyboard support
        btn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                btn.click();
            }
        });

        // Track hover for analytics/fun
        let hoverStart = 0;
        btn.addEventListener('mouseenter', () => {
            hoverStart = Date.now();
            btn.style.setProperty('--hover-duration', '0ms');
        });

        btn.addEventListener('mouseleave', () => {
            const duration = Date.now() - hoverStart;
            btn.style.setProperty('--hover-duration', `${duration}ms`);
        });
    }

    // ==========================================================================
    // Parallax Mouse Effect (for backgrounds)
    // ==========================================================================

    function initParallax(selector, strength = 0.1) {
        if (prefersReducedMotion) return;

        const elements = $$(selector);
        if (!elements.length) return;

        let mouseX = 0;
        let mouseY = 0;
        let currentX = 0;
        let currentY = 0;
        let rafId = null;

        function animate() {
            currentX = lerp(currentX, mouseX, 0.05);
            currentY = lerp(currentY, mouseY, 0.05);

            elements.forEach((el, i) => {
                const factor = strength * (i + 1) * 0.5;
                const x = currentX * factor;
                const y = currentY * factor;
                el.style.transform = `translate(${x}px, ${y}px)`;
            });

            rafId = requestAnimationFrame(animate);
        }

        document.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
            mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
        });

        animate();

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (rafId) cancelAnimationFrame(rafId);
        });
    }

    // ==========================================================================
    // Canvas Helpers
    // ==========================================================================

    function createCanvas(parent, className = '') {
        const canvas = document.createElement('canvas');
        canvas.className = className;
        parent.appendChild(canvas);
        return canvas;
    }

    function resizeCanvas(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        canvas.style.width = `${rect.width}px`;
        canvas.style.height = `${rect.height}px`;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        return { width: rect.width, height: rect.height, ctx };
    }

    // ==========================================================================
    // Particle System (Reusable)
    // ==========================================================================

    class ParticleSystem {
        constructor(canvas, options = {}) {
            this.canvas = canvas;
            this.ctx = canvas.getContext('2d');
            this.particles = [];
            this.options = {
                count: options.count || 100,
                color: options.color || 'var(--accent-primary)',
                minSize: options.minSize || 1,
                maxSize: options.maxSize || 3,
                speed: options.speed || 0.5,
                interaction: options.interaction !== false,
                ...options
            };
            this.mouse = { x: 0, y: 0, radius: 100 };
            this.width = 0;
            this.height = 0;
            this.animationId = null;
            this.init();
        }

        init() {
            this.resize();
            this.createParticles();
            this.bindEvents();
            this.animate();
        }

        resize() {
            const dpr = window.devicePixelRatio || 1;
            const rect = this.canvas.parentElement.getBoundingClientRect();
            this.width = rect.width;
            this.height = rect.height;
            this.canvas.width = this.width * dpr;
            this.canvas.height = this.height * dpr;
            this.canvas.style.width = `${this.width}px`;
            this.canvas.style.height = `${this.height}px`;
            this.ctx.scale(dpr, dpr);
        }

        createParticles() {
            this.particles = [];
            for (let i = 0; i < this.options.count; i++) {
                this.particles.push(this.createParticle());
            }
        }

        createParticle() {
            return {
                x: random(0, this.width),
                y: random(0, this.height),
                vx: random(-this.options.speed, this.options.speed),
                vy: random(-this.options.speed, this.options.speed),
                size: random(this.options.minSize, this.options.maxSize),
                opacity: random(0.2, 0.8),
                color: this.options.color
            };
        }

        bindEvents() {
            if (!this.options.interaction) return;

            this.canvas.addEventListener('mousemove', (e) => {
                const rect = this.canvas.getBoundingClientRect();
                this.mouse.x = e.clientX - rect.left;
                this.mouse.y = e.clientY - rect.top;
            });

            this.canvas.addEventListener('mouseleave', () => {
                this.mouse.x = -9999;
                this.mouse.y = -9999;
            });

            window.addEventListener('resize', () => this.resize());
        }

        update() {
            this.particles.forEach(p => {
                // Update position
                p.x += p.vx;
                p.y += p.vy;

                // Mouse interaction
                if (this.options.interaction) {
                    const dx = this.mouse.x - p.x;
                    const dy = this.mouse.y - p.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < this.mouse.radius && dist > 0) {
                        const force = (this.mouse.radius - dist) / this.mouse.radius * 0.5;
                        p.vx -= (dx / dist) * force;
                        p.vy -= (dy / dist) * force;
                    }
                }

                // Damping
                p.vx *= 0.99;
                p.vy *= 0.99;

                // Wrap around edges
                if (p.x < -p.size) p.x = this.width + p.size;
                if (p.x > this.width + p.size) p.x = -p.size;
                if (p.y < -p.size) p.y = this.height + p.size;
                if (p.y > this.height + p.size) p.y = -p.size;
            });
        }

        draw() {
            this.ctx.clearRect(0, 0, this.width, this.height);

            this.particles.forEach(p => {
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                this.ctx.fillStyle = this.hexToRgba(this.getColor(p.color), p.opacity);
                this.ctx.fill();
            });

            // Draw connections
            if (this.options.connections) {
                this.drawConnections();
            }
        }

        drawConnections() {
            const maxDist = this.options.connectionDistance || 120;
            this.ctx.strokeStyle = this.hexToRgba(this.getColor(this.options.color), 0.1);
            this.ctx.lineWidth = 0.5;

            for (let i = 0; i < this.particles.length; i++) {
                for (let j = i + 1; j < this.particles.length; j++) {
                    const dx = this.particles[i].x - this.particles[j].x;
                    const dy = this.particles[i].y - this.particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < maxDist) {
                        this.ctx.beginPath();
                        this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                        this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                        this.ctx.stroke();
                    }
                }
            }
        }

        getColor(color) {
            // Handle CSS variables
            if (color.startsWith('var(')) {
                const varName = color.match(/var\(--([^)]+)\)/);
                if (varName) {
                    return getComputedStyle(document.documentElement)
                        .getPropertyValue(`--${varName[1]}`).trim();
                }
            }
            return color;
        }

        hexToRgba(hex, alpha) {
            let r, g, b;
            if (hex.startsWith('#')) {
                const clean = hex.slice(1);
                if (clean.length === 3) {
                    r = parseInt(clean[0] + clean[0], 16);
                    g = parseInt(clean[1] + clean[1], 16);
                    b = parseInt(clean[2] + clean[2], 16);
                } else {
                    r = parseInt(clean.slice(0, 2), 16);
                    g = parseInt(clean.slice(2, 4), 16);
                    b = parseInt(clean.slice(4, 6), 16);
                }
            } else if (hex.startsWith('rgb')) {
                const match = hex.match(/\d+/g);
                if (match) [r, g, b] = match.map(Number);
            } else {
                // Default to accent primary
                r = 0; g = 212; b = 170;
            }
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }

        animate() {
            this.update();
            this.draw();
            this.animationId = requestAnimationFrame(() => this.animate());
        }

        destroy() {
            if (this.animationId) {
                cancelAnimationFrame(this.animationId);
            }
        }
    }

    // ==========================================================================
    // Intersection Observer for Scroll Animations
    // ==========================================================================

    function initScrollAnimations() {
        if (prefersReducedMotion) {
            $$('[data-scroll-animate]').forEach(el => el.classList.add('animate-fade-in'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '50px' });

        $$('[data-scroll-animate]').forEach(el => observer.observe(el));
    }

    // ==========================================================================
    // Initialize on DOM Ready
    // ==========================================================================

    function init() {
        enhanceGoBackButton();
        initScrollAnimations();

        // Expose utilities globally for error templates
        window.fbp = {
            random,
            randomInt,
            clamp,
            lerp,
            prefersReducedMotion,
            ParticleSystem,
            initParallax,
            createCanvas,
            resizeCanvas
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();