# fail-but-pretty

A FastAPI-based server with beautiful, interactive error pages that shuffle between 10 unique designs on every error. Features "Go Back" functionality to return to the previous page, deployed with easy-deploy and served via Caddy.

## Features

- **10 Unique Error Page Designs**: Each error triggers a randomly selected design:
  1. **Nebula** - Cosmic nebula with floating color clouds and twinkling stars
  2. **Geometric** - Floating geometric shapes over an animated grid
  3. **Matrix** - Classic Matrix rain with terminal output
  4. **Particles** - Interactive particle system (mouse attract/click repel)
  5. **Liquid** - Morphing organic blob animations with ripples
  6. **Terminal** - Retro terminal with scanlines and glitch effects
  7. **Aurora** - Aurora borealis waves with flowing gradients
  8. **Cyberpunk** - Perspective grid with glitch flashes and neon accents
  9. **Origami** - Floating paper shapes with fold animations
  10. **Constellation** - Click to create stars that form constellations

- **Go Back Functionality**: Smart navigation history tracking via sessions with referer fallback
- **Accessibility**: Respects `prefers-reduced-motion` and `prefers-color-scheme`
- **Zero-Config Deployment**: Uses easy-deploy with health checks, automatic rollback, Caddy reverse proxy
- **Health Check Endpoint**: `/health` for deployment monitoring

## Quick Start

### Local Development

```bash
# Clone and setup
git clone <your-repo>
cd fail-but-pretty

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The server will start at `http://localhost:8000`

### Using easy-deploy

```bash
# From the project directory
~/easy-deploy/init.sh
# Follow prompts (name: fail-but-pretty, stack: python, port: 8000)

# Commit and push
git add .
git commit -m "Initial commit"
git push

# On server
sudo deploy/install.sh --ci-key
# Set the 4 secrets printed in GitHub repository settings
```

## Project Structure

```
fail-but-pretty/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── installer.py            # easy-deploy Python environment manager
├── .env.example            # Environment variable template
├── deploy/                 # easy-deploy configuration
│   ├── easy-deploy.conf    # Deployment settings
│   ├── fail-but-pretty.service  # systemd unit
│   ├── fail-but-pretty.caddy    # Caddy site fragment
│   ├── deploy.sh           # Deploy engine (managed)
│   └── install.sh          # Install engine (managed)
├── static/
│   ├── css/
│   │   └── main.css        # Global styles & design tokens
│   └── js/
│       └── main.js         # Shared JS utilities
├── templates/
│   ├── base.html           # Base template with Go Back button
│   ├── index.html          # Home page with feature showcase
│   ├── demo.html           # Demo page for all error designs
│   ├── error_nebula.html
│   ├── error_geometric.html
│   ├── error_matrix.html
│   ├── error_particles.html
│   ├── error_liquid.html
│   ├── error_terminal.html
│   ├── error_aurora.html
│   ├── error_cyberpunk.html
│   ├── error_origami.html
│   └── error_constellation.html
└── .github/
    └── workflows/
        └── deploy.yml      # GitHub Actions workflow
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Home page with feature showcase |
| `/demo` | Interactive demo of all 10 error page designs |
| `/health` | Health check (returns JSON) |
| `/error/{code}` | Trigger a specific HTTP error (400, 401, 403, 404, 405, 408, 418, 422, 429, 500, 502, 503, 504) |
| `/preview/{template}?error_code=404` | Preview a specific error template |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Session secret for Go Back functionality | Required in production |
| `SITE` | Public domain for Caddy | Set via easy-deploy |

### easy-deploy Settings

Key settings in `deploy/easy-deploy.conf`:

```bash
NAME=fail-but-pretty
STACK=python
PORT=8030
SITE=fail.nebula-studios.net
SERVICE_USER=your-user
PREFIX=/srv/fail-but-pretty
HEALTH_URLS="http://127.0.0.1:8030/health http://127.0.0.1:8030/"
```

## Deployment Architecture

```
Internet → Caddy (port 80/443, TLS) → FastAPI (127.0.0.1:8030)
                                ↓
                        systemd service
                                ↓
                        easy-deploy (GitHub Actions)
```

- **Caddy**: Automatic HTTPS, reverse proxy, static file serving
- **FastAPI**: Runs on loopback only (port 8030), behind Caddy
- **systemd**: Manages the FastAPI process with security hardening
- **easy-deploy**: GitHub Actions → SSH → deploy.sh → health check → rollback on failure

## Customization

### Adding New Error Templates

1. Create a new template in `templates/error_new.html` extending `base.html`
2. Add the template name to `ERROR_TEMPLATES` in `main.py`
3. Add metadata to `TEMPLATE_METADATA` in `main.py` for the demo page

### Modifying Error Codes

Edit the `ERROR_CODES` dictionary in `main.py` to add/remove HTTP status codes.

## Accessibility

- All animations respect `prefers-reduced-motion: reduce`
- Color scheme respects `prefers-color-scheme: light`
- Semantic HTML with proper ARIA labels
- Keyboard navigable interactive elements
- Focus visible states

## Tech Stack

- **FastAPI** - Modern, fast web framework
- **Jinja2** - Template engine
- **Uvicorn** - ASGI server
- **Caddy** - Reverse proxy with automatic HTTPS
- **easy-deploy** - Deployment automation
- **systemd** - Service management
- **GitHub Actions** - CI/CD

## License

MIT License - Feel free to use this for your own projects!