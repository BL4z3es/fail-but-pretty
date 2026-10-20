"""
fail-but-pretty: A FastAPI server with beautiful, interactive error pages.

This project demonstrates how to create stunning error pages that shuffle
between different designs, each with unique interactive elements and a
"Go Back" functionality to return to the previous page.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
import random
import os
from http import HTTPStatus
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="fail-but-pretty",
    description="Beautiful, interactive error pages that shuffle on each error",
    version="1.0.0",
)

# Error page templates - 10 unique designs
ERROR_TEMPLATES = [
    "error_nebula.html",       # Cosmic nebula theme
    "error_geometric.html",    # Geometric shapes animation
    "error_matrix.html",       # Matrix rain effect
    "error_particles.html",    # Interactive particle system
    "error_liquid.html",       # Liquid/morphing blob animation
    "error_terminal.html",     # Retro terminal aesthetic
    "error_aurora.html",       # Aurora borealis waves
    "error_cyberpunk.html",    # Cyberpunk glitch effects
    "error_origami.html",      # Paper folding animations
    "error_constellation.html" # Star constellation drawing
]

ERROR_CODES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    418: "I'm a Teapot",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


def get_random_error_template() -> str:
    """Select a random error template from the available designs."""
    return random.choice(ERROR_TEMPLATES)


def get_previous_url(request: Request) -> str:
    """Get the previous URL from session or referer."""
    # Try to get from session history
    try:
        history = request.session.get("page_history", [])
        if len(history) >= 2:
            return history[-2]  # Second to last = previous page
    except (AssertionError, RuntimeError):
        pass  # Session not available

    # Fall back to referer
    referer = request.headers.get("referer")
    if referer:
        return referer

    # Default fallback
    return "/"


def update_page_history(request: Request, url: str):
    """Update the page history in session."""
    try:
        history = request.session.get("page_history", [])
        history.append(str(url))
        # Keep only last 10 pages
        if len(history) > 10:
            history = history[-10:]
        request.session["page_history"] = history
    except (AssertionError, RuntimeError):
        pass  # Session not available


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Add custom middleware FIRST (so it's outermost, runs after SessionMiddleware on request)
from starlette.middleware.base import BaseHTTPMiddleware


class PageHistoryMiddleware(BaseHTTPMiddleware):
    """Track page visits for 'Go Back' functionality."""

    async def dispatch(self, request: Request, call_next):
        # Only track GET requests that aren't static files or error pages
        path = request.url.path
        if request.method == "GET" and not path.startswith(("/static", "/error", "/render")):
            update_page_history(request, request.url)

        response = await call_next(request)
        return response


app.add_middleware(PageHistoryMiddleware)

# Add session middleware LAST (so it's innermost, runs first on request)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-in-production"),
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with beautiful error pages."""
    error_code = exc.status_code
    error_name = ERROR_CODES.get(error_code, "Unknown Error")
    error_detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    template = get_random_error_template()
    previous_url = get_previous_url(request)

    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "error_code": error_code,
            "error_name": error_name,
            "error_detail": error_detail,
            "previous_url": previous_url,
            "template_name": template,
        },
        status_code=error_code,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with a 500 error page."""
    error_code = 500
    error_name = ERROR_CODES[500]
    error_detail = str(exc)

    template = get_random_error_template()
    previous_url = get_previous_url(request)

    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "error_code": error_code,
            "error_name": error_name,
            "error_detail": error_detail,
            "previous_url": previous_url,
            "template_name": template,
        },
        status_code=500,
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "healthy", "service": "fail-but-pretty"}


# Root endpoint
@app.get("/")
async def root(request: Request):
    """Root endpoint - serves a demo page with links to trigger errors."""
    return templates.TemplateResponse("index.html", {"request": request, "error_codes": ERROR_CODES})


# Demo endpoints to trigger different errors
@app.get("/error/{error_code}")
async def trigger_error(error_code: int):
    """Trigger a specific HTTP error code for testing."""
    if error_code in ERROR_CODES:
        raise HTTPException(status_code=error_code, detail=f"This is a demo {ERROR_CODES[error_code]} error")
    raise HTTPException(status_code=404, detail=f"Error code {error_code} not found")


# Error pages for the other sites on this server. Caddy proxies a browser's
# failed page load here (see deploy/caddy/) and serves the answer under the
# failing site's own name, so this page cannot point at /static/: that path
# belongs to the site it is shown on. Its stylesheet and script go inline
# instead. Caddy drops the visitor's cookies on the way in and any Set-Cookie
# on the way out, and the history middleware above skips this path, so a
# visitor on another site never carries this app's session.
BASE_DIR = Path(__file__).resolve().parent
INLINE_CSS = (BASE_DIR / "static/css/main.css").read_text()
INLINE_JS = (BASE_DIR / "static/js/main.js").read_text()

RENDER_DETAILS = {
    400: "The request could not be understood.",
    401: "You need to sign in to see this page.",
    403: "You do not have access to this page.",
    404: "There is nothing at this address.",
    405: "This page does not accept that kind of request.",
    408: "The request took too long.",
    410: "This page is gone for good.",
    429: "Too many requests. Wait a moment and try again.",
    500: "Something broke on our side.",
    502: "The service behind this page is not answering. It may be restarting.",
    503: "The service is unavailable right now. Try again shortly.",
    504: "The service took too long to answer.",
}


# HEAD too: Caddy forwards a HEAD for a page as it came, and @app.get alone answers it 405.
@app.api_route("/render/{error_code}", methods=["GET", "HEAD"])
async def render_error(error_code: int, request: Request):
    """Render an error page for another site, at that site's status code."""
    if not 400 <= error_code <= 599:
        error_code = 500
    try:
        phrase = HTTPStatus(error_code).phrase
    except ValueError:
        phrase = "Client Error" if error_code < 500 else "Server Error"
    error_name = ERROR_CODES.get(error_code, phrase)
    detail = RENDER_DETAILS.get(error_code, "Something went wrong with this request.")
    template = get_random_error_template()

    response = templates.TemplateResponse(
        template,
        {
            "request": request,
            "error_code": error_code,
            "error_name": error_name,
            "error_detail": detail,
            # The page linking here, on the failing site; that site's home otherwise.
            "previous_url": request.headers.get("referer") or "/",
            "template_name": template,
            "inline_css": INLINE_CSS,
            "inline_js": INLINE_JS,
        },
        status_code=error_code,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


# Template metadata for demo page
TEMPLATE_METADATA = [
    {
        "name": "Nebula",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>',
        "colors": {"primary": "#00d4aa", "secondary": "#6366f1"},
        "description": "Cosmic nebula with floating color clouds and twinkling stars."
    },
    {
        "name": "Geometric",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon><line x1="12" y1="22" x2="12" y2="15.5"></line><polyline points="22 8.5 12 15.5 2 8.5"></polyline></svg>',
        "colors": {"primary": "#6366f1", "secondary": "#f43f5e"},
        "description": "Floating geometric shapes (triangles, squares, circles, hexagons) over a grid."
    },
    {
        "name": "Matrix",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>',
        "colors": {"primary": "#00d4aa", "secondary": "#006644"},
        "description": "Classic Matrix rain with falling katakana and terminal output."
    },
    {
        "name": "Particles",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="5" r="1"></circle><circle cx="5" cy="19" r="1"></circle><circle cx="19" cy="19" r="1"></circle><circle cx="5" cy="5" r="1"></circle></svg>',
        "colors": {"primary": "#fbbf24", "secondary": "#f43f5e"},
        "description": "Interactive particle system - move mouse to attract, click to repel."
    },
    {
        "name": "Liquid",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2c5.5 0 10 4.5 10 10s-4.5 10-10 10S2 17.5 2 12 6.5 2 12 2"></path><path d="M12 6v6l4 2"></path></svg>',
        "colors": {"primary": "#00d4aa", "secondary": "#6366f1"},
        "description": "Morphing liquid blobs with organic blob animations and ripples."
    },
    {
        "name": "Terminal",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>',
        "colors": {"primary": "#58a6ff", "secondary": "#27ca4f"},
        "description": "Retro terminal with scanlines, glitch effects, and command output."
    },
    {
        "name": "Aurora",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>',
        "colors": {"primary": "#6366f1", "secondary": "#f43f5e"},
        "description": "Aurora borealis waves with flowing gradient colors and star trails."
    },
    {
        "name": "Cyberpunk",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="1" width="22" height="22" rx="2"></rect><line x1="1" y1="12" x2="23" y2="12"></line><line x1="12" y1="1" x2="12" y2="23"></line></svg>',
        "colors": {"primary": "#f43f5e", "secondary": "#00d4aa"},
        "description": "Cyberpunk grid with perspective, glitch flashes, and neon accents."
    },
    {
        "name": "Origami",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polyline><line x1="12" y1="22" x2="12" y2="15.5"></line><polyline points="22 8.5 12 15.5 2 8.5"></polyline></svg>',
        "colors": {"primary": "#1a1a2e", "secondary": "#2a2a4e"},
        "description": "Floating paper shapes with fold animations and subtle shadows."
    },
    {
        "name": "Constellation",
        "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 2 15 8 18 12 15 16 12 2 9 8 6 12 9 16"></polyline></svg>',
        "colors": {"primary": "#00d4aa", "secondary": "#fbbf24"},
        "description": "Click to create stars that automatically connect into constellations."
    }
]

# Demo page to showcase all error pages
@app.get("/demo")
async def demo_page(request: Request):
    """Demo page showing all error page designs."""
    return templates.TemplateResponse("demo.html", {
        "request": request,
        "error_codes": ERROR_CODES,
        "templates": ERROR_TEMPLATES,
        "template_metadata": TEMPLATE_METADATA,
        "template_data": list(zip(ERROR_TEMPLATES, TEMPLATE_METADATA)),
    })


# Preview a specific error template
@app.get("/preview/{template_name}")
async def preview_template(template_name: str, request: Request, error_code: int = 404):
    """Preview a specific error template with a given error code."""
    if template_name not in ERROR_TEMPLATES:
        template_name = ERROR_TEMPLATES[0]

    if error_code not in ERROR_CODES:
        error_code = 404

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "error_code": error_code,
            "error_name": ERROR_CODES[error_code],
            "error_detail": f"This is a preview of {ERROR_CODES[error_code]}",
            "previous_url": "/demo",
            "template_name": template_name,
            "is_preview": True,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)