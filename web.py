"""
AfroMations - AI Documentary & Clipping Studio
World-Class Design Implementation

Design Philosophy:
- Museum-quality software, not SaaS clutter
- Steve Krug's "Don't Make Me Think" principles
- Motion Primitives + TweakCN inspired components
- One dominant focal area per screen
- Progressive disclosure
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn


class Settings:
    """Application settings from environment variables"""
    PORT: int = int(os.environ.get('PORT', 8080))
    HOST: str = os.environ.get('HOST', '0.0.0.0')
    DEBUG: bool = os.environ.get('DEBUG', 'false').lower() == 'true'
    GOOGLE_CLIENT_ID: str = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    SESSION_SECRET: str = os.environ.get('SESSION_SECRET', secrets.token_hex(32))
    LEMON_SQUEEZY_API_KEY: str = os.environ.get('LEMON_SQUEEZY_API_KEY', '')
    LEMON_SQUEEZY_STORE_ID: str = os.environ.get('LEMON_SQUEEZY_STORE_ID', '')
    LEMON_SQUEEZY_WEBHOOK_SECRET: str = os.environ.get('LEMON_SQUEEZY_WEBHOOK_SECRET', '')
    SUPABASE_URL: str = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY: str = os.environ.get('SUPABASE_ANON_KEY', '')
    SENTRY_DSN: str = os.environ.get('SENTRY_DSN', '')
    GROQ_API_KEY: str = os.environ.get('GROQ_API_KEY', '')
    WHISPER_MODEL: str = os.environ.get('WHISPER_MODEL', 'base')
    INVITE_ONLY: bool = os.environ.get('INVITE_ONLY', 'true').lower() == 'true'

    @classmethod
    def is_configured(cls, *keys: str) -> bool:
        for key in keys:
            value = getattr(cls, key, '')
            if not value or value.startswith('stub') or value.startswith('placeholder'):
                return False
        return True

settings = Settings()

app = FastAPI(
    title="AfroMations",
    description="AI Documentary & Clipping Studio for Seattle/Washington Creators",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, Dict[str, Any]] = {}
invites: Dict[str, Dict[str, Any]] = {}
users: Dict[str, Dict[str, Any]] = {}


class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None
    use_case: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    invite_code: Optional[str] = None

class ClipRequest(BaseModel):
    video_url: Optional[str] = None
    query: str
    output_format: str = "mp4"

class WebhookPayload(BaseModel):
    meta: Dict[str, Any]
    data: Dict[str, Any]


# =============================================================================
# DESIGN SYSTEM CONSTANTS
# =============================================================================

DESIGN_SYSTEM = {
    "colors": {
        "primary": "#1a1a1a",      # Near black - text
        "accent": "#2d5a27",        # Forest green - cultural, grounded
        "accent_light": "#4a8f42",  # Lighter green for hover
        "background": "#fafafa",    # Warm white
        "surface": "#ffffff",       # Pure white for cards
        "muted": "#64748b",         # Slate gray for secondary text
        "border": "#e2e8f0",        # Light border
        "success": "#22c55e",
        "error": "#ef4444",
    },
    "typography": {
        "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "font_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    },
    "spacing": {
        "xs": "0.25rem",
        "sm": "0.5rem",
        "md": "1rem",
        "lg": "1.5rem",
        "xl": "2rem",
        "2xl": "3rem",
        "3xl": "4rem",
    },
    "animation": {
        "fast": "150ms",
        "normal": "250ms",
        "slow": "400ms",
        "easing": "cubic-bezier(0.4, 0, 0.2, 1)",
    }
}


# =============================================================================
# CSS STYLES - Motion Primitives Inspired
# =============================================================================

def get_base_styles() -> str:
    """Generate base CSS with design system tokens"""
    return f'''
    :root {{
        --color-primary: {DESIGN_SYSTEM["colors"]["primary"]};
        --color-accent: {DESIGN_SYSTEM["colors"]["accent"]};
        --color-accent-light: {DESIGN_SYSTEM["colors"]["accent_light"]};
        --color-background: {DESIGN_SYSTEM["colors"]["background"]};
        --color-surface: {DESIGN_SYSTEM["colors"]["surface"]};
        --color-muted: {DESIGN_SYSTEM["colors"]["muted"]};
        --color-border: {DESIGN_SYSTEM["colors"]["border"]};
        --font-family: {DESIGN_SYSTEM["typography"]["font_family"]};
        --transition-fast: {DESIGN_SYSTEM["animation"]["fast"]};
        --transition-normal: {DESIGN_SYSTEM["animation"]["normal"]};
        --transition-slow: {DESIGN_SYSTEM["animation"]["slow"]};
        --easing: {DESIGN_SYSTEM["animation"]["easing"]};
    }}

    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    html {{
        font-size: 16px;
        scroll-behavior: smooth;
    }}

    body {{
        font-family: var(--font-family);
        background: var(--color-background);
        color: var(--color-primary);
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}

    /* Focus states for accessibility */
    :focus-visible {{
        outline: 2px solid var(--color-accent);
        outline-offset: 2px;
    }}

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }}
    }}

    /* Typography Scale */
    .text-display {{
        font-size: clamp(3rem, 8vw, 5.5rem);
        font-weight: 300;
        line-height: 1.05;
        letter-spacing: -0.03em;
    }}

    .text-headline {{
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 400;
        line-height: 1.15;
        letter-spacing: -0.02em;
    }}

    .text-title {{
        font-size: 1.5rem;
        font-weight: 500;
        line-height: 1.3;
        letter-spacing: -0.01em;
    }}

    .text-body {{
        font-size: 1.125rem;
        font-weight: 400;
        line-height: 1.6;
    }}

    .text-small {{
        font-size: 0.875rem;
        font-weight: 400;
        line-height: 1.5;
    }}

    .text-caption {{
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}

    .text-muted {{
        color: var(--color-muted);
    }}

    .text-accent {{
        color: var(--color-accent);
    }}

    /* Layout Utilities */
    .container {{
        width: 100%;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1.5rem;
    }}

    .container-narrow {{
        max-width: 800px;
    }}

    /* Motion Primitives - Fade In Up */
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(24px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    .animate-fade-in-up {{
        animation: fadeInUp 0.6s var(--easing) forwards;
    }}

    .animate-delay-1 {{ animation-delay: 0.1s; opacity: 0; }}
    .animate-delay-2 {{ animation-delay: 0.2s; opacity: 0; }}
    .animate-delay-3 {{ animation-delay: 0.3s; opacity: 0; }}
    .animate-delay-4 {{ animation-delay: 0.4s; opacity: 0; }}

    /* Motion Primitives - Blur In */
    @keyframes blurIn {{
        from {{
            opacity: 0;
            filter: blur(8px);
        }}
        to {{
            opacity: 1;
            filter: blur(0);
        }}
    }}

    .animate-blur-in {{
        animation: blurIn 0.8s var(--easing) forwards;
    }}

    /* Button Component - TweakCN Style */
    .btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.875rem 1.75rem;
        font-family: var(--font-family);
        font-size: 0.875rem;
        font-weight: 600;
        letter-spacing: 0.025em;
        text-decoration: none;
        border: none;
        border-radius: 0;
        cursor: pointer;
        transition: all var(--transition-normal) var(--easing);
        position: relative;
        overflow: hidden;
    }}

    .btn-primary {{
        background: var(--color-primary);
        color: var(--color-background);
    }}

    .btn-primary:hover {{
        background: var(--color-accent);
        transform: translateY(-2px);
    }}

    .btn-primary:active {{
        transform: translateY(0);
    }}

    .btn-secondary {{
        background: transparent;
        color: var(--color-primary);
        border: 1px solid var(--color-border);
    }}

    .btn-secondary:hover {{
        border-color: var(--color-primary);
        background: var(--color-primary);
        color: var(--color-background);
    }}

    .btn-ghost {{
        background: transparent;
        color: var(--color-muted);
        padding: 0.5rem 1rem;
    }}

    .btn-ghost:hover {{
        color: var(--color-primary);
    }}

    /* Icon styling */
    .btn svg {{
        width: 16px;
        height: 16px;
        transition: transform var(--transition-fast) var(--easing);
    }}

    .btn:hover svg {{
        transform: translateX(4px);
    }}

    /* Card Component */
    .card {{
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        padding: 1.5rem;
        transition: all var(--transition-normal) var(--easing);
    }}

    .card:hover {{
        border-color: var(--color-muted);
    }}

    .card-interactive {{
        cursor: pointer;
    }}

    .card-interactive:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04);
    }}

    /* Navigation */
    .nav {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 100;
        padding: 1rem 0;
        background: rgba(250, 250, 250, 0.8);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid transparent;
        transition: all var(--transition-normal) var(--easing);
    }}

    .nav.scrolled {{
        border-bottom-color: var(--color-border);
    }}

    .nav-inner {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .nav-logo {{
        font-size: 1.125rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--color-primary);
        text-decoration: none;
    }}

    .nav-links {{
        display: flex;
        align-items: center;
        gap: 2rem;
    }}

    .nav-link {{
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--color-muted);
        text-decoration: none;
        transition: color var(--transition-fast) var(--easing);
    }}

    .nav-link:hover {{
        color: var(--color-primary);
    }}

    /* Hero Section - Full viewport, single focus */
    .hero {{
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 6rem 0 4rem;
        position: relative;
    }}

    .hero-content {{
        max-width: 900px;
    }}

    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.75rem;
        background: rgba(45, 90, 39, 0.08);
        color: var(--color-accent);
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }}

    .hero-title {{
        margin-bottom: 1.5rem;
    }}

    .hero-title strong {{
        font-weight: 600;
    }}

    .hero-description {{
        max-width: 600px;
        margin-bottom: 2.5rem;
    }}

    .hero-cta {{
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }}

    /* Features Section - Minimal, scannable */
    .features {{
        padding: 6rem 0;
        border-top: 1px solid var(--color-border);
    }}

    .features-header {{
        max-width: 600px;
        margin-bottom: 4rem;
    }}

    .features-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 2rem;
    }}

    .feature {{
        padding: 1.5rem 0;
    }}

    .feature-icon {{
        width: 40px;
        height: 40px;
        margin-bottom: 1rem;
        color: var(--color-accent);
    }}

    .feature-title {{
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}

    .feature-description {{
        font-size: 0.9375rem;
        color: var(--color-muted);
        line-height: 1.6;
    }}

    /* Social Proof Section */
    .social-proof {{
        padding: 4rem 0;
        background: var(--color-surface);
        border-top: 1px solid var(--color-border);
        border-bottom: 1px solid var(--color-border);
    }}

    .social-proof-content {{
        text-align: center;
    }}

    .social-proof-stat {{
        font-size: 3rem;
        font-weight: 300;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }}

    /* Positioning Section - The "Why Different" */
    .positioning {{
        padding: 6rem 0;
    }}

    .positioning-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4rem;
        align-items: start;
    }}

    .positioning-column {{
        padding: 2rem;
    }}

    .positioning-column.them {{
        background: #f1f5f9;
        border: 1px solid var(--color-border);
    }}

    .positioning-column.us {{
        background: rgba(45, 90, 39, 0.04);
        border: 1px solid var(--color-accent);
    }}

    .positioning-label {{
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }}

    .positioning-column.them .positioning-label {{
        color: var(--color-muted);
    }}

    .positioning-column.us .positioning-label {{
        color: var(--color-accent);
    }}

    /* CTA Section */
    .cta-section {{
        padding: 6rem 0;
        text-align: center;
        border-top: 1px solid var(--color-border);
    }}

    .cta-content {{
        max-width: 600px;
        margin: 0 auto;
    }}

    /* Footer */
    .footer {{
        padding: 3rem 0;
        border-top: 1px solid var(--color-border);
    }}

    .footer-inner {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .footer-text {{
        font-size: 0.875rem;
        color: var(--color-muted);
    }}

    .footer-links {{
        display: flex;
        gap: 1.5rem;
    }}

    .footer-link {{
        font-size: 0.875rem;
        color: var(--color-muted);
        text-decoration: none;
        transition: color var(--transition-fast) var(--easing);
    }}

    .footer-link:hover {{
        color: var(--color-primary);
    }}

    /* Responsive */
    @media (max-width: 768px) {{
        .nav-links {{
            display: none;
        }}

        .hero {{
            padding: 5rem 0 3rem;
        }}

        .positioning-grid {{
            grid-template-columns: 1fr;
            gap: 2rem;
        }}

        .footer-inner {{
            flex-direction: column;
            gap: 1.5rem;
            text-align: center;
        }}
    }}

    /* Invite Badge - Floating */
    .invite-badge {{
        position: fixed;
        top: 50%;
        right: -36px;
        transform: rotate(-90deg) translateX(-50%);
        background: var(--color-accent);
        color: white;
        padding: 0.5rem 1.25rem;
        font-size: 0.625rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        z-index: 50;
    }}

    @media (max-width: 768px) {{
        .invite-badge {{
            display: none;
        }}
    }}

    /* Form Styles */
    .form-group {{
        margin-bottom: 1.5rem;
    }}

    .form-label {{
        display: block;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }}

    .form-input {{
        width: 100%;
        padding: 0.875rem 1rem;
        font-family: var(--font-family);
        font-size: 1rem;
        border: 1px solid var(--color-border);
        background: var(--color-surface);
        transition: border-color var(--transition-fast) var(--easing);
    }}

    .form-input:focus {{
        outline: none;
        border-color: var(--color-accent);
    }}

    .form-input::placeholder {{
        color: var(--color-muted);
    }}
    '''


# =============================================================================
# HERO PAGE - Landing
# =============================================================================

def get_hero_page() -> str:
    """Generate the full-page hero landing page with world-class design"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AfroMations | The AI Archive That Finds Your Story</title>
    <meta name="description" content="Turn years of footage into searchable chapters. AI-powered footage intelligence for documentary creators, cultural archivists, and production teams.">
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{DESIGN_SYSTEM["typography"]["font_import"]}" rel="stylesheet">
    
    <style>
        {get_base_styles()}
    </style>
</head>
<body>
    <!-- Navigation - Minimal, non-intrusive -->
    <nav class="nav" id="nav">
        <div class="container">
            <div class="nav-inner">
                <a href="/" class="nav-logo">AfroMations</a>
                <div class="nav-links">
                    <a href="#features" class="nav-link">Features</a>
                    <a href="#positioning" class="nav-link">Why Us</a>
                    <a href="/app" class="btn btn-primary">Request Access</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Invite Badge -->
    <div class="invite-badge">Seattle Creators</div>

    <!-- Hero Section - Single dominant focal area -->
    <section class="hero">
        <div class="container">
            <div class="hero-content">
                <!-- Badge - Establishes context immediately -->
                <div class="hero-badge animate-fade-in-up">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    Footage Intelligence Platform
                </div>
                
                <!-- Headline - The one thing they need to understand -->
                <h1 class="text-display hero-title animate-fade-in-up animate-delay-1">
                    Turn years of footage<br>into <strong>searchable chapters</strong>
                </h1>
                
                <!-- Description - Clarifies the value -->
                <p class="text-body text-muted hero-description animate-fade-in-up animate-delay-2">
                    The AI archive that finds your story. Index everything you've ever shot, 
                    search by concept or emotion, and ship compelling content in hours—not weeks.
                </p>
                
                <!-- CTA - One primary action -->
                <div class="hero-cta animate-fade-in-up animate-delay-3">
                    <a href="/app" class="btn btn-primary">
                        Explore
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M5 12h14M12 5l7 7-7 7"/>
                        </svg>
                    </a>
                    <a href="#features" class="btn btn-secondary">Learn More</a>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section - Scannable, minimal -->
    <section class="features" id="features">
        <div class="container">
            <div class="features-header">
                <p class="text-caption text-accent" style="margin-bottom: 1rem;">What We Solve</p>
                <h2 class="text-headline">The footage graveyard problem</h2>
                <p class="text-body text-muted" style="margin-top: 1rem;">
                    Documentary creators have terabytes of footage they can't search. 
                    It sits on hard drives, unsearchable, unusable. We fix that.
                </p>
            </div>
            
            <div class="features-grid">
                <!-- Feature 1 -->
                <div class="feature">
                    <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="M21 21l-4.35-4.35"/>
                    </svg>
                    <h3 class="feature-title">Search Everything</h3>
                    <p class="feature-description">
                        "Find every moment someone mentions gentrification" across 5 years of footage. 
                        Search by concept, emotion, or spoken word.
                    </p>
                </div>
                
                <!-- Feature 2 -->
                <div class="feature">
                    <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18M9 21V9"/>
                    </svg>
                    <h3 class="feature-title">AI Pre-Screening</h3>
                    <p class="feature-description">
                        Professional editors spend 60-80% of time in review. 
                        Our AI surfaces relevant moments, turning weeks into hours.
                    </p>
                </div>
                
                <!-- Feature 3 -->
                <div class="feature">
                    <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M12 2a10 10 0 1 0 10 10"/>
                        <path d="M12 12l4-4"/>
                        <path d="M16 4v4h4"/>
                    </svg>
                    <h3 class="feature-title">Multilingual Pipeline</h3>
                    <p class="feature-description">
                        Dual subtitles and AI dubbing in one workflow. 
                        Reach global audiences without vendor wrangling.
                    </p>
                </div>
                
                <!-- Feature 4 -->
                <div class="feature">
                    <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                    </svg>
                    <h3 class="feature-title">Viral Scoring</h3>
                    <p class="feature-description">
                        Know what will perform before you publish. 
                        AI-powered predictions and A/B testing for thumbnails and titles.
                    </p>
                </div>
            </div>
        </div>
    </section>

    <!-- Positioning Section - Why we're different -->
    <section class="positioning" id="positioning">
        <div class="container">
            <div class="features-header" style="margin-bottom: 3rem;">
                <p class="text-caption text-accent" style="margin-bottom: 1rem;">The Difference</p>
                <h2 class="text-headline">We're not a video editor</h2>
            </div>
            
            <div class="positioning-grid">
                <div class="positioning-column them">
                    <p class="positioning-label">Video Editors (CapCut, etc.)</p>
                    <p class="text-title" style="margin-bottom: 1rem;">"I have a clip, make it pretty"</p>
                    <ul style="list-style: none; color: var(--color-muted);">
                        <li style="margin-bottom: 0.5rem;">• Template-driven editing</li>
                        <li style="margin-bottom: 0.5rem;">• Assumes you know what clip you want</li>
                        <li style="margin-bottom: 0.5rem;">• Consumer/influencer focused</li>
                        <li style="margin-bottom: 0.5rem;">• Quick social media clips</li>
                    </ul>
                </div>
                
                <div class="positioning-column us">
                    <p class="positioning-label">AfroMations</p>
                    <p class="text-title" style="margin-bottom: 1rem;">"I have 500 hours, find me the story"</p>
                    <ul style="list-style: none; color: var(--color-primary);">
                        <li style="margin-bottom: 0.5rem;">• AI-powered footage discovery</li>
                        <li style="margin-bottom: 0.5rem;">• Searches your entire archive</li>
                        <li style="margin-bottom: 0.5rem;">• Production teams & archivists</li>
                        <li style="margin-bottom: 0.5rem;">• Documentary-grade storytelling</li>
                    </ul>
                </div>
            </div>
        </div>
    </section>

    <!-- Social Proof -->
    <section class="social-proof">
        <div class="container">
            <div class="social-proof-content">
                <p class="text-caption text-muted" style="margin-bottom: 1rem;">Built For</p>
                <p class="social-proof-stat">Seattle & I-5 Corridor Creators</p>
                <p class="text-body text-muted">
                    Documentary filmmakers, cultural archivists, and production teams 
                    who have too much footage and not enough time.
                </p>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
        <div class="container">
            <div class="cta-content">
                <p class="text-caption text-accent" style="margin-bottom: 1rem;">Limited Access</p>
                <h2 class="text-headline" style="margin-bottom: 1rem;">Ready to find your story?</h2>
                <p class="text-body text-muted" style="margin-bottom: 2rem;">
                    We're opening access in limited waves to Seattle-area creators. 
                    Request an invite to join the first cohort.
                </p>
                <a href="/app" class="btn btn-primary">
                    Request Access
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                </a>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-inner">
                <p class="footer-text">© 2024 AfroMations. Built for creators in the I-5 corridor.</p>
                <div class="footer-links">
                    <a href="/pricing" class="footer-link">Pricing</a>
                    <a href="https://github.com/executiveusa/AFRO-CLIPZ" class="footer-link">GitHub</a>
                </div>
            </div>
        </div>
    </footer>

    <script>
        // Minimal JS - Navigation scroll effect
        const nav = document.getElementById('nav');
        window.addEventListener('scroll', () => {{
            if (window.scrollY > 50) {{
                nav.classList.add('scrolled');
            }} else {{
                nav.classList.remove('scrolled');
            }}
        }});

        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>'''


# =============================================================================
# APP DASHBOARD - Clean, minimal, one action per view
# =============================================================================

def get_app_dashboard() -> str:
    """Generate the app dashboard with world-class design"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard | AfroMations</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{DESIGN_SYSTEM["typography"]["font_import"]}" rel="stylesheet">
    
    <style>
        {get_base_styles()}
        
        /* Dashboard-specific styles */
        .dashboard {{
            min-height: 100vh;
            padding-top: 5rem;
        }}
        
        .dashboard-header {{
            padding: 3rem 0;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .dashboard-header-inner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .dashboard-content {{
            padding: 3rem 0;
        }}
        
        /* Empty State - The hero of the dashboard */
        .empty-state {{
            text-align: center;
            padding: 6rem 2rem;
            max-width: 500px;
            margin: 0 auto;
        }}
        
        .empty-state-icon {{
            width: 64px;
            height: 64px;
            margin: 0 auto 1.5rem;
            color: var(--color-muted);
            opacity: 0.5;
        }}
        
        /* Project Grid */
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        
        .project-card {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            padding: 1.5rem;
            cursor: pointer;
            transition: all var(--transition-normal) var(--easing);
        }}
        
        .project-card:hover {{
            border-color: var(--color-accent);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04);
        }}
        
        .project-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }}
        
        .project-card-title {{
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        
        .project-card-meta {{
            font-size: 0.875rem;
            color: var(--color-muted);
        }}
        
        .project-card-stats {{
            display: flex;
            gap: 1.5rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--color-border);
        }}
        
        .project-stat {{
            font-size: 0.875rem;
        }}
        
        .project-stat-value {{
            font-weight: 600;
            color: var(--color-primary);
        }}
        
        .project-stat-label {{
            color: var(--color-muted);
        }}
        
        /* Upload Zone */
        .upload-zone {{
            border: 2px dashed var(--color-border);
            padding: 3rem;
            text-align: center;
            cursor: pointer;
            transition: all var(--transition-normal) var(--easing);
        }}
        
        .upload-zone:hover {{
            border-color: var(--color-accent);
            background: rgba(45, 90, 39, 0.02);
        }}
        
        .upload-zone-icon {{
            width: 48px;
            height: 48px;
            margin: 0 auto 1rem;
            color: var(--color-muted);
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="nav scrolled">
        <div class="container">
            <div class="nav-inner">
                <a href="/" class="nav-logo">AfroMations</a>
                <div class="nav-links">
                    <a href="/app" class="nav-link" style="color: var(--color-primary);">Projects</a>
                    <a href="/app/library" class="nav-link">Library</a>
                    <a href="/app/settings" class="nav-link">Settings</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="dashboard">
        <div class="container">
            <!-- Dashboard Header -->
            <div class="dashboard-header">
                <div class="dashboard-header-inner">
                    <div>
                        <h1 class="text-headline">Projects</h1>
                        <p class="text-body text-muted">Your footage archives and clip projects</p>
                    </div>
                    <button class="btn btn-primary" onclick="showNewProject()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 5v14M5 12h14"/>
                        </svg>
                        New Project
                    </button>
                </div>
            </div>
            
            <!-- Dashboard Content -->
            <div class="dashboard-content">
                <!-- Empty State (shown when no projects) -->
                <div class="empty-state" id="emptyState">
                    <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18"/>
                        <path d="M9 21V9"/>
                    </svg>
                    <h2 class="text-title" style="margin-bottom: 0.5rem;">No projects yet</h2>
                    <p class="text-body text-muted" style="margin-bottom: 1.5rem;">
                        Create your first project to start indexing footage and finding stories.
                    </p>
                    <button class="btn btn-primary" onclick="showNewProject()">
                        Create First Project
                    </button>
                </div>
                
                <!-- Projects Grid (hidden when empty) -->
                <div class="projects-grid" id="projectsGrid" style="display: none;">
                    <!-- Sample Project Card -->
                    <div class="project-card card-interactive">
                        <div class="project-card-header">
                            <div>
                                <h3 class="project-card-title">Seattle Documentary 2024</h3>
                                <p class="project-card-meta">Updated 2 hours ago</p>
                            </div>
                            <span class="text-caption" style="color: var(--color-accent);">Active</span>
                        </div>
                        <div class="project-card-stats">
                            <div class="project-stat">
                                <span class="project-stat-value">47</span>
                                <span class="project-stat-label"> hours indexed</span>
                            </div>
                            <div class="project-stat">
                                <span class="project-stat-value">12</span>
                                <span class="project-stat-label"> clips found</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- New Project Modal (hidden by default) -->
    <div id="newProjectModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; align-items: center; justify-content: center;">
        <div style="background: var(--color-surface); padding: 2rem; max-width: 500px; width: 90%; margin: 2rem;">
            <h2 class="text-title" style="margin-bottom: 1.5rem;">New Project</h2>
            
            <div class="form-group">
                <label class="form-label" for="projectName">Project Name</label>
                <input type="text" id="projectName" class="form-input" placeholder="e.g., Seattle Documentary 2024">
            </div>
            
            <div class="form-group">
                <label class="form-label">Upload Footage</label>
                <div class="upload-zone">
                    <svg class="upload-zone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    <p class="text-body">Drop video files here or click to browse</p>
                    <p class="text-small text-muted">MP4, MOV, AVI up to 10GB</p>
                </div>
            </div>
            
            <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 2rem;">
                <button class="btn btn-secondary" onclick="hideNewProject()">Cancel</button>
                <button class="btn btn-primary">Create Project</button>
            </div>
        </div>
    </div>

    <script>
        function showNewProject() {{
            document.getElementById('newProjectModal').style.display = 'flex';
        }}
        
        function hideNewProject() {{
            document.getElementById('newProjectModal').style.display = 'none';
        }}
        
        // Close modal on backdrop click
        document.getElementById('newProjectModal').addEventListener('click', function(e) {{
            if (e.target === this) hideNewProject();
        }});
    </script>
</body>
</html>'''


# =============================================================================
# PRICING PAGE
# =============================================================================

def get_pricing_page() -> str:
    """Generate the pricing page"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pricing | AfroMations</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{DESIGN_SYSTEM["typography"]["font_import"]}" rel="stylesheet">
    
    <style>
        {get_base_styles()}
        
        .pricing {{
            padding: 8rem 0 4rem;
        }}
        
        .pricing-header {{
            text-align: center;
            max-width: 600px;
            margin: 0 auto 4rem;
        }}
        
        .pricing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .pricing-card {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            padding: 2rem;
            display: flex;
            flex-direction: column;
        }}
        
        .pricing-card.featured {{
            border-color: var(--color-accent);
            position: relative;
        }}
        
        .pricing-card.featured::before {{
            content: 'Most Popular';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--color-accent);
            color: white;
            padding: 0.25rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        
        .pricing-card-header {{
            margin-bottom: 1.5rem;
        }}
        
        .pricing-card-name {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .pricing-card-description {{
            font-size: 0.9375rem;
            color: var(--color-muted);
        }}
        
        .pricing-card-price {{
            margin-bottom: 1.5rem;
        }}
        
        .pricing-amount {{
            font-size: 3rem;
            font-weight: 300;
            letter-spacing: -0.02em;
        }}
        
        .pricing-period {{
            font-size: 0.875rem;
            color: var(--color-muted);
        }}
        
        .pricing-features {{
            list-style: none;
            margin-bottom: 2rem;
            flex-grow: 1;
        }}
        
        .pricing-features li {{
            padding: 0.5rem 0;
            font-size: 0.9375rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .pricing-features li svg {{
            width: 16px;
            height: 16px;
            color: var(--color-accent);
            flex-shrink: 0;
        }}
        
        .pricing-note {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--color-border);
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="nav" id="nav">
        <div class="container">
            <div class="nav-inner">
                <a href="/" class="nav-logo">AfroMations</a>
                <div class="nav-links">
                    <a href="/#features" class="nav-link">Features</a>
                    <a href="/pricing" class="nav-link" style="color: var(--color-primary);">Pricing</a>
                    <a href="/app" class="btn btn-primary">Request Access</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="pricing">
        <div class="container">
            <div class="pricing-header">
                <p class="text-caption text-accent" style="margin-bottom: 1rem;">Pricing</p>
                <h1 class="text-headline" style="margin-bottom: 1rem;">Outcomes, not features</h1>
                <p class="text-body text-muted">
                    Annual plans only. We're building for serious creators who want results, 
                    not another monthly subscription to forget about.
                </p>
            </div>
            
            <div class="pricing-grid">
                <!-- Creator Pro -->
                <div class="pricing-card">
                    <div class="pricing-card-header">
                        <h2 class="pricing-card-name">Creator Pro</h2>
                        <p class="pricing-card-description">Your AI assistant editor + localization studio</p>
                    </div>
                    <div class="pricing-card-price">
                        <span class="pricing-amount">$200</span>
                        <span class="pricing-period">/month, billed annually</span>
                    </div>
                    <ul class="pricing-features">
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            600 minutes of video/month
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            AI transcription & search
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Smart clipping
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Dual subtitles (2 languages)
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            3 team seats
                        </li>
                    </ul>
                    <a href="/app" class="btn btn-secondary" style="width: 100%;">Request Access</a>
                </div>
                
                <!-- Studio -->
                <div class="pricing-card featured">
                    <div class="pricing-card-header">
                        <h2 class="pricing-card-name">Studio</h2>
                        <p class="pricing-card-description">Pixar-style departments in a box</p>
                    </div>
                    <div class="pricing-card-price">
                        <span class="pricing-amount">$800</span>
                        <span class="pricing-period">/month, billed annually</span>
                    </div>
                    <ul class="pricing-features">
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            3,000 minutes of video/month
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Everything in Creator Pro
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            AI dubbing (2 languages)
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Viral scoring & ranking
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            YouTube publishing
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            10 team seats
                        </li>
                    </ul>
                    <a href="/app" class="btn btn-primary" style="width: 100%;">Request Access</a>
                </div>
                
                <!-- Black Label -->
                <div class="pricing-card">
                    <div class="pricing-card-header">
                        <h2 class="pricing-card-name">Black Label</h2>
                        <p class="pricing-card-description">Autonomous studio ops + private deployment</p>
                    </div>
                    <div class="pricing-card-price">
                        <span class="pricing-amount">Custom</span>
                        <span class="pricing-period">starting at $3,000/month</span>
                    </div>
                    <ul class="pricing-features">
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Unlimited video processing
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Everything in Studio
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Dedicated deployment
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Custom AI agents
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            White-label option
                        </li>
                        <li>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            SLA support
                        </li>
                    </ul>
                    <a href="mailto:hello@afromations.com" class="btn btn-secondary" style="width: 100%;">Contact Us</a>
                </div>
            </div>
            
            <div class="pricing-note">
                <p class="text-body text-muted">
                    All plans require an invite. We're opening access in limited waves to ensure quality.
                </p>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-inner">
                <p class="footer-text">© 2024 AfroMations. Built for creators in the I-5 corridor.</p>
                <div class="footer-links">
                    <a href="/" class="footer-link">Home</a>
                    <a href="https://github.com/executiveusa/AFRO-CLIPZ" class="footer-link">GitHub</a>
                </div>
            </div>
        </div>
    </footer>

    <script>
        const nav = document.getElementById('nav');
        window.addEventListener('scroll', () => {{
            if (window.scrollY > 50) {{
                nav.classList.add('scrolled');
            }} else {{
                nav.classList.remove('scrolled');
            }}
        }});
    </script>
</body>
</html>'''


# =============================================================================
# API ROUTES
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the hero landing page"""
    return get_hero_page()

@app.get("/app", response_class=HTMLResponse)
async def dashboard():
    """Serve the app dashboard"""
    return get_app_dashboard()

@app.get("/pricing", response_class=HTMLResponse)
async def pricing():
    """Serve the pricing page"""
    return get_pricing_page()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "design_system": "motion-primitives-inspired"
    }

@app.post("/api/invite/request")
async def request_invite(request: InviteRequest):
    """Request an invite to the platform"""
    invite_id = hashlib.sha256(f"{request.email}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
    invites[invite_id] = {
        "email": request.email,
        "name": request.name,
        "company": request.company,
        "use_case": request.use_case,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    return {
        "success": True,
        "message": "Invite request received. We'll be in touch soon.",
        "request_id": invite_id
    }

@app.post("/api/clip")
async def create_clip(request: ClipRequest):
    """Create a new clip job"""
    job_id = secrets.token_hex(8)
    return {
        "job_id": job_id,
        "status": "queued",
        "query": request.query,
        "message": "Clip job created. Processing will begin shortly."
    }

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a clip job"""
    return {
        "job_id": job_id,
        "status": "processing",
        "progress": 45,
        "message": "Analyzing footage..."
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "web_redesign:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
