# RepoRouge 🔴

A modern, lightweight Git alternative for code management, collaboration, and version control. RepoRouge provides a seamless experience for developers to manage repositories with an intuitive web interface and powerful CLI tools.

### Live Preview:
https://reporouge.netlify.app/

## ✨ Features
 
### 🌐 Web Platform
- **Repository Management** - Create, clone, and manage repositories with ease
- **Branch Management** - Create, switch, and delete branches
- **File Operations** - Create, edit, delete, and view files directly in the browser
- **Real-time Collaboration** - Add collaborators with granular permissions (read/write/admin)
- **Private & Public Repos** - Full control over repository visibility

### 🖥️ RepoRouge CLI
- **Git-like Commands** - Familiar commands for developers (`clone`, `push`, `pull`, `status`, etc.)
- **Auto-dependency Management** - CLI automatically installs required dependencies

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB instance

#### CLI Setup
```bash
# Download the CLI tool
wget https://your-domain.com/reporouge_cli.py

# Make it executable (Linux/macOS)
chmod +x reporouge_cli.py

# Or run directly with Python
python reporouge_cli.py --help
```

## 🛠️ Tech Stack

### Frontend
- **React** - Modern UI library for building interactive interfaces
- **Tailwind CSS** - Utility-first CSS framework for styling
- **React Router** - Client-side routing
- **Axios** - HTTP client for API requests

### Backend
- **FastAPI** - High-performance Python web framework
- **Motor** - Async MongoDB driver for Python
- **JWT** - JSON Web Tokens for authentication
- **BCrypt** - Password hashing
- **Uvicorn** - ASGI server for production

### Database
- **MongoDB** - NoSQL database for flexible document storage
- **Motor** - Async MongoDB operations

### CLI Tool
- **Click** - Python package for creating command-line interfaces
- **Requests** - HTTP library for API interactions
- **Auto-installer** - Automatic dependency management

## 📖 Usage

### Web Interface

1. **Register/Login** - Create an account or sign in
2. **Create Repository** - Start a new project or import existing code
3. **Collaborate** - Add team members with appropriate permissions
4. **Branch & Merge** - Use branching strategies for feature development
5. **File Management** - Edit files directly in the browser

### CLI Commands

```bash
# Login to RepoRouge
python reporouge_cli.py login

# Clone a repository
python reporouge_cli.py clone owner/repo-name

# Check repository status
python reporouge_cli.py status

# List branches
python reporouge_cli.py branch --all

# Switch branches
python reporouge_cli.py checkout feature-branch

# Push changes
python reporouge_cli.py push -m "Your commit message"

# Pull latest changes
python reporouge_cli.py pull
```

## 🐛 Bug Reports & Feature Requests

Please use the [GitHub Issues](https://github.com/y4th4rthh/reporouge/issues) page to report bugs or request features.

## 🙏 Acknowledgments

- Thanks to all contributors who helped build RepoRouge
- Inspired by Git and modern development workflows
- Built with love for the developer community

---
