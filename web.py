"""
AfroMations - AI Documentary & Clipping Studio
FastAPI Web Application

This is the main web server that serves:
- Hero landing page
- Authentication (Google OAuth)
- Billing integration (Lemon Squeezy)
- Clip API endpoints
- Dashboard
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

# ============================================================================
# Configuration
# ============================================================================

class Settings:
    """Application settings from environment variables"""

    # Server
    PORT: int = int(os.environ.get('PORT', 8080))
    HOST: str = os.environ.get('HOST', '0.0.0.0')
    DEBUG: bool = os.environ.get('DEBUG', 'false').lower() == 'true'

    # Auth
    GOOGLE_CLIENT_ID: str = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    SESSION_SECRET: str = os.environ.get('SESSION_SECRET', secrets.token_hex(32))

    # Billing
    LEMON_SQUEEZY_API_KEY: str = os.environ.get('LEMON_SQUEEZY_API_KEY', '')
    LEMON_SQUEEZY_STORE_ID: str = os.environ.get('LEMON_SQUEEZY_STORE_ID', '')
    LEMON_SQUEEZY_WEBHOOK_SECRET: str = os.environ.get('LEMON_SQUEEZY_WEBHOOK_SECRET', '')

    # Database (Supabase)
    SUPABASE_URL: str = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY: str = os.environ.get('SUPABASE_ANON_KEY', '')

    # Observability
    SENTRY_DSN: str = os.environ.get('SENTRY_DSN', '')

    # AI/ML
    GROQ_API_KEY: str = os.environ.get('GROQ_API_KEY', '')
    WHISPER_MODEL: str = os.environ.get('WHISPER_MODEL', 'base')

    # Feature flags
    INVITE_ONLY: bool = os.environ.get('INVITE_ONLY', 'true').lower() == 'true'

    @classmethod
    def is_configured(cls, *keys: str) -> bool:
        """Check if all specified settings are configured"""
        for key in keys:
            value = getattr(cls, key, '')
            if not value or value.startswith('stub') or value.startswith('placeholder'):
                return False
        return True

settings = Settings()

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AfroMations",
    description="AI Documentary & Clipping Studio for Seattle/Washington Creators",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# In-Memory Session Store (replace with Redis/DB in production)
# ============================================================================

sessions: Dict[str, Dict[str, Any]] = {}
invites: Dict[str, Dict[str, Any]] = {}  # invite_code -> {email, plan, created_at}
users: Dict[str, Dict[str, Any]] = {}  # user_id -> user data

# ============================================================================
# Pydantic Models
# ============================================================================

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

# ============================================================================
# HTML Templates
# ============================================================================

def get_hero_page() -> str:
    """Generate the full-page hero landing page"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AfroMations | AI Documentary Studio</title>
    <meta name="description" content="AI-powered documentary and clipping studio for Seattle/Washington creators. Transform years of footage into compelling stories.">

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --color-bg: #fafafa;
            --color-text: #1a1a1a;
            --color-accent: #2d5a27;
            --color-accent-light: #4a8f42;
            --color-gray: #666;
            --color-gray-light: #e5e5e5;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body {
            height: 100%;
            font-family: var(--font-main);
            background: var(--color-bg);
            color: var(--color-text);
            overflow-x: hidden;
        }

        /* Hero Section - Full Page */
        .hero {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
            padding: 2rem;
            text-align: center;
        }

        /* Minimal Navigation */
        .nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            padding: 1.5rem 3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
            background: rgba(250, 250, 250, 0.9);
            backdrop-filter: blur(10px);
        }

        .logo {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: var(--color-text);
            text-decoration: none;
        }

        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }

        .nav-links a {
            color: var(--color-gray);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: color 0.2s;
        }

        .nav-links a:hover {
            color: var(--color-text);
        }

        /* Hero Content */
        .hero-content {
            max-width: 800px;
            margin: 0 auto;
        }

        .hero-tagline {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            color: var(--color-accent);
            margin-bottom: 1.5rem;
            font-weight: 600;
        }

        .hero-title {
            font-size: clamp(2.5rem, 8vw, 5rem);
            font-weight: 300;
            line-height: 1.1;
            margin-bottom: 1.5rem;
            letter-spacing: -0.03em;
        }

        .hero-title strong {
            font-weight: 600;
        }

        .hero-description {
            font-size: 1.125rem;
            color: var(--color-gray);
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto 3rem;
        }

        /* CTA Button */
        .cta-button {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            background: var(--color-text);
            color: var(--color-bg);
            padding: 1rem 2.5rem;
            font-size: 0.875rem;
            font-weight: 600;
            text-decoration: none;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }

        .cta-button:hover {
            background: var(--color-accent);
            transform: translateY(-2px);
        }

        .cta-button svg {
            width: 16px;
            height: 16px;
            transition: transform 0.3s;
        }

        .cta-button:hover svg {
            transform: translateX(4px);
        }

        /* Features Grid */
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 3rem;
            max-width: 900px;
            margin: 6rem auto 0;
            padding-top: 3rem;
            border-top: 1px solid var(--color-gray-light);
        }

        .feature {
            text-align: left;
        }

        .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        .feature h3 {
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            letter-spacing: -0.01em;
        }

        .feature p {
            font-size: 0.8125rem;
            color: var(--color-gray);
            line-height: 1.5;
        }

        /* Footer */
        .footer {
            position: absolute;
            bottom: 2rem;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 0.75rem;
            color: var(--color-gray);
        }

        .footer a {
            color: var(--color-gray);
            text-decoration: none;
        }

        .footer a:hover {
            color: var(--color-text);
        }

        /* Invite Badge */
        .invite-badge {
            position: fixed;
            top: 50%;
            right: -40px;
            transform: rotate(-90deg) translateX(-50%);
            background: var(--color-accent);
            color: white;
            padding: 0.5rem 1.5rem;
            font-size: 0.625rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-weight: 600;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .nav {
                padding: 1rem 1.5rem;
            }

            .nav-links {
                display: none;
            }

            .hero {
                padding: 1rem;
            }

            .features {
                gap: 2rem;
                margin-top: 4rem;
            }

            .invite-badge {
                display: none;
            }
        }

        /* Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .hero-content {
            animation: fadeIn 0.8s ease-out;
        }

        .features {
            animation: fadeIn 1s ease-out 0.3s both;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="nav">
        <a href="/" class="logo">AfroMations</a>
        <div class="nav-links">
            <a href="#features">Features</a>
            <a href="/pricing">Pricing</a>
            <a href="/login">Sign In</a>
        </div>
    </nav>

    <!-- Invite Badge -->
    <div class="invite-badge">Seattle Creators</div>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <p class="hero-tagline">AI Documentary Studio</p>
            <h1 class="hero-title">
                Transform your <strong>footage</strong><br>into <strong>stories</strong>
            </h1>
            <p class="hero-description">
                An AI-powered studio for Seattle and Washington creators.
                Index years of footage, find the moments that matter,
                and ship compelling content in hours, not weeks.
            </p>
            <a href="/app" class="cta-button">
                Explore
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
            </a>
        </div>

        <!-- Features -->
        <div class="features" id="features">
            <div class="feature">
                <div class="feature-icon">🎬</div>
                <h3>Smart Indexing</h3>
                <p>Transcribe and search through years of footage in seconds.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">✂️</div>
                <h3>AI Clipping</h3>
                <p>Describe what you want. Get clips that match.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🌍</div>
                <h3>Multilingual</h3>
                <p>Dual subtitles and dubbing for global reach.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📈</div>
                <h3>Viral Scoring</h3>
                <p>AI-powered predictions for content performance.</p>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <p>&copy; 2024 AfroMations. Built for creators in the I-5 corridor.</p>
        </footer>
    </section>

    <script>
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>'''

def get_app_dashboard() -> str:
    """Generate the app dashboard page"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard | AfroMations</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --color-bg: #fafafa;
            --color-text: #1a1a1a;
            --color-accent: #2d5a27;
            --color-gray: #666;
            --color-gray-light: #e5e5e5;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        body {
            font-family: var(--font-main);
            background: var(--color-bg);
            color: var(--color-text);
            min-height: 100vh;
        }
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }
        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
        }
        .dashboard-header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        .btn {
            background: var(--color-text);
            color: var(--color-bg);
            padding: 0.75rem 1.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            text-decoration: none;
            border: none;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn:hover { background: var(--color-accent); }
        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        .project-card {
            background: white;
            border: 1px solid var(--color-gray-light);
            padding: 1.5rem;
            transition: box-shadow 0.2s;
        }
        .project-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        .project-card h3 {
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }
        .project-card p {
            font-size: 0.875rem;
            color: var(--color-gray);
        }
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            background: white;
            border: 2px dashed var(--color-gray-light);
        }
        .empty-state h2 {
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
        }
        .empty-state p {
            color: var(--color-gray);
            margin-bottom: 1.5rem;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 2rem;
            color: var(--color-gray);
            text-decoration: none;
            font-size: 0.875rem;
        }
        .back-link:hover { color: var(--color-text); }
    </style>
</head>
<body>
    <div class="dashboard">
        <a href="/" class="back-link">&larr; Back to home</a>
        <div class="dashboard-header">
            <h1>Your Projects</h1>
            <button class="btn" onclick="createProject()">New Project</button>
        </div>

        <div class="empty-state">
            <h2>No projects yet</h2>
            <p>Create your first project to start transforming your footage.</p>
            <button class="btn" onclick="createProject()">Create Project</button>
        </div>
    </div>

    <script>
        function createProject() {
            window.location.href = '/app/new';
        }
    </script>
</body>
</html>'''

def get_login_page() -> str:
    """Generate the login page"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign In | AfroMations</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --color-bg: #fafafa;
            --color-text: #1a1a1a;
            --color-accent: #2d5a27;
            --color-gray: #666;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        body {
            font-family: var(--font-main);
            background: var(--color-bg);
            color: var(--color-text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            width: 100%;
            max-width: 400px;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .login-header p {
            color: var(--color-gray);
            font-size: 0.875rem;
        }
        .login-form {
            background: white;
            padding: 2rem;
            border: 1px solid #e5e5e5;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            font-size: 1rem;
            border: 1px solid #e5e5e5;
            font-family: inherit;
        }
        .form-group input:focus {
            outline: none;
            border-color: var(--color-accent);
        }
        .btn {
            width: 100%;
            background: var(--color-text);
            color: var(--color-bg);
            padding: 0.875rem;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: none;
            cursor: pointer;
            margin-top: 1rem;
        }
        .btn:hover { background: var(--color-accent); }
        .divider {
            text-align: center;
            margin: 1.5rem 0;
            color: var(--color-gray);
            font-size: 0.75rem;
        }
        .google-btn {
            width: 100%;
            background: white;
            color: var(--color-text);
            padding: 0.875rem;
            font-size: 0.875rem;
            font-weight: 500;
            border: 1px solid #e5e5e5;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
        }
        .google-btn:hover { background: #f5f5f5; }
        .back-link {
            display: block;
            text-align: center;
            margin-top: 1.5rem;
            color: var(--color-gray);
            text-decoration: none;
            font-size: 0.875rem;
        }
        .invite-notice {
            background: #f0f7ef;
            border: 1px solid #d4e5d1;
            padding: 1rem;
            margin-bottom: 1.5rem;
            font-size: 0.875rem;
            color: var(--color-accent);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>Welcome back</h1>
            <p>Sign in to continue to AfroMations</p>
        </div>

        <div class="login-form">
            <div class="invite-notice">
                AfroMations is currently invite-only. Request access to join the Seattle Creator Cohort.
            </div>

            <button class="google-btn" onclick="signInWithGoogle()">
                <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
            </button>

            <div class="divider">or</div>

            <form onsubmit="signInWithEmail(event)">
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" required placeholder="you@example.com">
                </div>
                <div class="form-group">
                    <label>Invite Code</label>
                    <input type="text" name="invite_code" placeholder="Enter your invite code">
                </div>
                <button type="submit" class="btn">Continue</button>
            </form>
        </div>

        <a href="/" class="back-link">&larr; Back to home</a>
    </div>

    <script>
        function signInWithGoogle() {
            window.location.href = '/auth/google';
        }

        function signInWithEmail(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            window.location.href = '/auth/email?email=' + encodeURIComponent(formData.get('email')) + '&code=' + encodeURIComponent(formData.get('invite_code'));
        }
    </script>
</body>
</html>'''

def get_pricing_page() -> str:
    """Generate the pricing page"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pricing | AfroMations</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --color-bg: #fafafa;
            --color-text: #1a1a1a;
            --color-accent: #2d5a27;
            --color-gray: #666;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        body {
            font-family: var(--font-main);
            background: var(--color-bg);
            color: var(--color-text);
            min-height: 100vh;
        }
        .nav {
            padding: 1.5rem 3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e5e5e5;
        }
        .logo {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--color-text);
            text-decoration: none;
        }
        .pricing-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }
        .pricing-header {
            text-align: center;
            margin-bottom: 4rem;
        }
        .pricing-header h1 {
            font-size: 2.5rem;
            font-weight: 300;
            margin-bottom: 1rem;
        }
        .pricing-header p {
            color: var(--color-gray);
            font-size: 1.125rem;
        }
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
        }
        .pricing-card {
            background: white;
            border: 1px solid #e5e5e5;
            padding: 2.5rem;
            position: relative;
        }
        .pricing-card.featured {
            border-color: var(--color-accent);
            box-shadow: 0 4px 20px rgba(45, 90, 39, 0.1);
        }
        .pricing-card.featured::before {
            content: 'Most Popular';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--color-accent);
            color: white;
            padding: 0.25rem 1rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .plan-name {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .plan-desc {
            color: var(--color-gray);
            font-size: 0.875rem;
            margin-bottom: 1.5rem;
        }
        .plan-price {
            font-size: 3rem;
            font-weight: 300;
            margin-bottom: 0.5rem;
        }
        .plan-price span {
            font-size: 1rem;
            color: var(--color-gray);
        }
        .plan-period {
            color: var(--color-gray);
            font-size: 0.875rem;
            margin-bottom: 2rem;
        }
        .plan-features {
            list-style: none;
            margin-bottom: 2rem;
        }
        .plan-features li {
            padding: 0.5rem 0;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .plan-features li::before {
            content: '✓';
            color: var(--color-accent);
            font-weight: bold;
        }
        .btn {
            width: 100%;
            background: var(--color-text);
            color: var(--color-bg);
            padding: 1rem;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: none;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            display: block;
        }
        .btn:hover { background: var(--color-accent); }
        .btn-outline {
            background: transparent;
            color: var(--color-text);
            border: 1px solid var(--color-text);
        }
        .btn-outline:hover {
            background: var(--color-text);
            color: var(--color-bg);
        }
        .notice {
            text-align: center;
            margin-top: 3rem;
            padding: 1.5rem;
            background: #f5f5f5;
            font-size: 0.875rem;
            color: var(--color-gray);
        }
    </style>
</head>
<body>
    <nav class="nav">
        <a href="/" class="logo">AfroMations</a>
    </nav>

    <div class="pricing-container">
        <div class="pricing-header">
            <h1>Simple, outcome-based pricing</h1>
            <p>Annual and 2-year plans only. We sell results, not seats.</p>
        </div>

        <div class="pricing-grid">
            <!-- Creator Pro -->
            <div class="pricing-card">
                <h2 class="plan-name">Creator Pro</h2>
                <p class="plan-desc">For solo creators and small teams</p>
                <div class="plan-price">$2,400<span>/year</span></div>
                <p class="plan-period">$200/mo effective &bull; 2-year: $4,200</p>
                <ul class="plan-features">
                    <li>3 team seats</li>
                    <li>10 projects</li>
                    <li>600 minutes/month processing</li>
                    <li>AI transcription & clipping</li>
                    <li>2-language subtitles</li>
                    <li>YouTube integration</li>
                </ul>
                <a href="/checkout/creator_pro" class="btn btn-outline">Get Started</a>
            </div>

            <!-- Studio -->
            <div class="pricing-card featured">
                <h2 class="plan-name">Studio</h2>
                <p class="plan-desc">For production teams and agencies</p>
                <div class="plan-price">$9,600<span>/year</span></div>
                <p class="plan-period">$800/mo effective &bull; 2-year: $16,800</p>
                <ul class="plan-features">
                    <li>10 team seats</li>
                    <li>50 projects</li>
                    <li>3,000 minutes/month processing</li>
                    <li>Multi-source ingest (Drive, OneDrive)</li>
                    <li>4-language subtitles + 2 dubbed</li>
                    <li>Viral scoring & recommendations</li>
                    <li>Basic white-label</li>
                    <li>Priority processing</li>
                </ul>
                <a href="/checkout/studio" class="btn">Get Started</a>
            </div>

            <!-- Black Label -->
            <div class="pricing-card">
                <h2 class="plan-name">Black Label</h2>
                <p class="plan-desc">For media companies and archives</p>
                <div class="plan-price">$36,000<span>+/year</span></div>
                <p class="plan-period">Custom &bull; Contact for 2-year pricing</p>
                <ul class="plan-features">
                    <li>Unlimited seats</li>
                    <li>Unlimited projects</li>
                    <li>Dedicated deployment</li>
                    <li>Custom AI agents</li>
                    <li>Full white-label</li>
                    <li>SLA support</li>
                    <li>Agent training loops</li>
                </ul>
                <a href="/contact" class="btn btn-outline">Contact Us</a>
            </div>
        </div>

        <div class="notice">
            AfroMations is invite-only. All plans require annual or 2-year commitment.<br>
            No monthly plans. No discounts. Results-focused pricing.
        </div>
    </div>
</body>
</html>'''

# ============================================================================
# Routes - Pages
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Hero landing page"""
    return get_hero_page()

@app.get("/app", response_class=HTMLResponse)
async def dashboard():
    """App dashboard"""
    return get_app_dashboard()

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    return get_login_page()

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page():
    """Pricing page"""
    return get_pricing_page()

# ============================================================================
# Routes - API
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "afromations",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "auth_configured": settings.is_configured('GOOGLE_CLIENT_ID'),
            "billing_configured": settings.is_configured('LEMON_SQUEEZY_API_KEY'),
            "db_configured": settings.is_configured('SUPABASE_URL'),
            "ai_configured": settings.is_configured('GROQ_API_KEY'),
        }
    }

@app.get("/api/config")
async def get_public_config():
    """Public configuration for frontend"""
    return {
        "invite_only": settings.INVITE_ONLY,
        "google_auth_enabled": bool(settings.GOOGLE_CLIENT_ID),
        "features": {
            "clipping": True,
            "transcription": True,
            "subtitles": True,
            "dubbing": False,  # Phase 2
            "viral_scoring": False,  # Phase 2
        }
    }

# ============================================================================
# Routes - Auth (Placeholder - integrate with Supabase/Google OAuth)
# ============================================================================

@app.get("/auth/google")
async def google_auth():
    """Initiate Google OAuth flow"""
    if not settings.GOOGLE_CLIENT_ID:
        return JSONResponse(
            status_code=501,
            content={"error": "Google Auth not configured", "message": "Set GOOGLE_CLIENT_ID environment variable"}
        )
    # In production, redirect to Google OAuth
    return RedirectResponse(url="/app")

@app.get("/auth/email")
async def email_auth(email: str, code: Optional[str] = None):
    """Email authentication with invite code"""
    if settings.INVITE_ONLY and not code:
        return JSONResponse(
            status_code=403,
            content={"error": "Invite required", "message": "AfroMations is invite-only. Please provide an invite code."}
        )
    # In production, verify invite code and send magic link
    return RedirectResponse(url="/app")

# ============================================================================
# Routes - Billing (Lemon Squeezy integration)
# ============================================================================

@app.get("/checkout/{plan_id}")
async def create_checkout(plan_id: str):
    """Create Lemon Squeezy checkout session"""
    if not settings.LEMON_SQUEEZY_API_KEY:
        return JSONResponse(
            status_code=501,
            content={"error": "Billing not configured", "message": "Set LEMON_SQUEEZY_API_KEY environment variable"}
        )

    # Plan mapping
    plans = {
        "creator_pro": {"variant_id": "123", "name": "Creator Pro"},
        "studio": {"variant_id": "456", "name": "Studio"},
        "black_label": {"variant_id": "789", "name": "Black Label"},
    }

    if plan_id not in plans:
        raise HTTPException(status_code=404, detail="Plan not found")

    # In production, create checkout via Lemon Squeezy API
    return JSONResponse(content={
        "message": "Checkout would be created here",
        "plan": plans[plan_id],
        "redirect_url": f"https://afromations.lemonsqueezy.com/checkout/{plan_id}"
    })

@app.post("/webhooks/lemon-squeezy")
async def lemon_squeezy_webhook(request: Request):
    """Handle Lemon Squeezy webhooks"""
    # Verify webhook signature
    signature = request.headers.get("X-Signature")
    body = await request.body()

    if settings.LEMON_SQUEEZY_WEBHOOK_SECRET:
        expected_sig = hashlib.hmac(
            settings.LEMON_SQUEEZY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        if signature != expected_sig:
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event_name = payload.get("meta", {}).get("event_name")

    # Handle different webhook events
    if event_name == "subscription_created":
        # Activate subscription
        pass
    elif event_name == "subscription_updated":
        # Update subscription
        pass
    elif event_name == "subscription_cancelled":
        # Handle cancellation
        pass

    return {"received": True}

# ============================================================================
# Routes - Clip API (integrates with existing clipper)
# ============================================================================

@app.post("/api/clip")
async def create_clip(clip_request: ClipRequest, background_tasks: BackgroundTasks):
    """Create a clip from video based on query"""
    # This would integrate with the existing app_enhanced.py clipper
    job_id = secrets.token_hex(8)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Clip job created",
        "query": clip_request.query,
        "estimated_time": "2-5 minutes",
        "status_url": f"/api/jobs/{job_id}"
    }

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    # In production, check job queue/database
    return {
        "job_id": job_id,
        "status": "processing",
        "progress": 45,
        "message": "Transcribing video..."
    }

# ============================================================================
# Static Files
# ============================================================================

# Mount assets directory if it exists
assets_path = Path(__file__).parent / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎬 AfroMations - AI Documentary Studio")
    print("="*60)
    print(f"Server: http://{settings.HOST}:{settings.PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Invite Only: {settings.INVITE_ONLY}")
    print("="*60 + "\n")

    uvicorn.run(
        "web:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
