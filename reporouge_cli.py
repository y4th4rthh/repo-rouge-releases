#!/usr/bin/env python3
"""
RepoRouge CLI Tool
A Git-like CLI for RepoRouge repositories
Run directly without installation: python reporouge_cli.py
"""

import sys
import subprocess
import importlib.util

# Auto-install required packages
REQUIRED_PACKAGES = {
    'click': 'click>=8.0.0',
    'requests': 'requests>=2.25.0'
}

def install_package(package_name, package_spec):
    """Install a package using pip"""
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', package_spec
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install_dependencies():
    """Check and auto-install required dependencies"""
    missing_packages = []
    
    for package_name, package_spec in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(package_name) is None:
            missing_packages.append((package_name, package_spec))
    
    if missing_packages:
        print("🔧 Installing required dependencies...")
        for package_name, package_spec in missing_packages:
            print(f"   Installing {package_name}...")
            if install_package(package_name, package_spec):
                print(f"   ✅ {package_name} installed successfully")
            else:
                print(f"   ❌ Failed to install {package_name}")
                print(f"   Please run: pip install {package_spec}")
                sys.exit(1)
        print("🎉 All dependencies installed!")

# Install dependencies before importing them
check_and_install_dependencies()

import click
import requests
import json
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import difflib
from datetime import datetime

# Configuration
CLI_VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".reporouge"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"

class RepoRougeConfig:
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self.cache_dir = CACHE_DIR
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Ensure config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {"server_url": "https://repo-rouge.onrender.com", "token": None, "username": None}
        
        try:
            with open(str(self.config_file), 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # If config file is corrupted, return default config
            return {"server_url": "https://repo-rouge.onrender.com", "token": None, "username": None}
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            # Ensure the parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(str(self.config_file), 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            raise click.ClickException(f"Failed to save configuration: {e}")
    
    def get_local_repo_config(self) -> Optional[Dict[str, Any]]:
        """Get local repository configuration"""
        repo_config_path = Path(".reporouge") / "config.json"
        if repo_config_path.exists():
            try:
                with open(str(repo_config_path), 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

class RepoRougeAPI:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login to RepoRouge"""
        response = self.session.post(f"{self.base_url}/auth/login", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        return response.json()
    
    def get_cli_token(self) -> Dict[str, Any]:
        """Get CLI token for long-term usage"""
        response = self.session.post(f"{self.base_url}/auth/cli-token")
        response.raise_for_status()
        return response.json()
    
    def clone_repo(self, owner: str, repo_name: str, branch: str = "main") -> bytes:
        """Clone repository as ZIP"""
        response = self.session.get(f"{self.base_url}/api/repos/{owner}/{repo_name}/clone?branch={branch}")
        response.raise_for_status()
        return response.content
    
    def get_repo_info(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Get repository information"""
        response = self.session.get(f"{self.base_url}/api/repos/{owner}/{repo_name}/info")
        response.raise_for_status()
        return response.json()
    
    def get_branches(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Get repository branches"""
        response = self.session.get(f"{self.base_url}/repos/{repo_name}/branches")
        response.raise_for_status()
        return response.json()
    
    def switch_branch(self, owner: str, repo_name: str, branch: str) -> Dict[str, Any]:
        """Switch to a branch"""
        response = self.session.post(f"{self.base_url}/repos/{repo_name}/branches/{branch}/switch")
        response.raise_for_status()
        return response.json()
    
    def push_files(self, owner: str, repo_name: str, files: list, branch: str = "main") -> Dict[str, Any]:
        """Push files to repository"""
        response = self.session.post(f"{self.base_url}/api/repos/{owner}/{repo_name}/push", json=files, params={"branch": branch})
        response.raise_for_status()
        return response.json()
    
    def get_file_diff(self, owner: str, repo_name: str, file_path: str, branch: str = "main") -> Dict[str, Any]:
        """Get file for diff comparison"""
        response = self.session.get(f"{self.base_url}/api/repos/{owner}/{repo_name}/diff", params={
            "file_path": file_path,
            "branch": branch
        })
        response.raise_for_status()
        return response.json()

# CLI Context
@click.group()
@click.version_option(version=CLI_VERSION)
@click.pass_context
def cli(ctx):
    """RepoRouge CLI - A Git-like interface for RepoRouge repositories"""
    ctx.ensure_object(dict)
    try:
        config_manager = RepoRougeConfig()
        ctx.obj['config'] = config_manager
        
        # Auto-setup on first run
        if not config_manager.config_file.exists():
            click.echo("🚀 Welcome to RepoRouge CLI!")
            click.echo("This appears to be your first time running the CLI.")
            click.echo(f"Configuration directory created at: {str(config_manager.config_dir)}")
            click.echo("💡 To get started:")
            click.echo("1. Run 'python reporouge_cli.py login' to authenticate")
            click.echo("2. Run 'python reporouge_cli.py clone owner/repo-name' to clone a repository")
            click.echo("3. Use 'python reporouge_cli.py --help' to see all available commands")
            click.echo()
            
            # Create initial config
            initial_config = {
                "server_url": "https://repo-rouge.onrender.com",
                "token": None,
                "username": None,
                "setup_completed": True
            }
            config_manager.save_config(initial_config)
    except Exception as e:
        click.echo(f"❌ Failed to initialize configuration: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--email', prompt=True, help='Your email address')
@click.option('--password', prompt=True, hide_input=True, help='Your password')
@click.option('--server', default='https://repo-rouge.onrender.com', help='Server URL')
@click.pass_context
def login(ctx, email: str, password: str, server: str):
    """Login to RepoRouge"""
    config_manager = ctx.obj['config']
    api = RepoRougeAPI(server)
    
    try:
        # Login and get token
        login_response = api.login(email, password)
        api.token = login_response['access_token']
        api.session.headers.update({"Authorization": f"Bearer {api.token}"})
        
        # Get CLI token for long-term usage
        cli_token_response = api.get_cli_token()
        
        # Save configuration
        config = {
            "server_url": server,
            "token": cli_token_response['cli_token'],
            "username": login_response['user']['username'],
            "email": login_response['user']['email']
        }
        config_manager.save_config(config)
        
        click.echo(f"✅ Successfully logged in as {login_response['user']['username']}")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Login failed: {e}", err=True)

@cli.command()
@click.argument('repo_url')  # Format: owner/repo-name
@click.option('--branch', default='main', help='Branch to clone')
@click.option('--directory', help='Directory to clone into')
@click.pass_context
def clone(ctx, repo_url: str, branch: str, directory: Optional[str]):
    """Clone a repository"""
    config_manager = ctx.obj['config']
    config = config_manager.load_config()
    
    if not config.get('token'):
        click.echo("❌ Please login first using 'python reporouge_cli.py login'", err=True)
        return
    
    try:
        owner, repo_name = repo_url.split('/', 1)
    except ValueError:
        click.echo("❌ Invalid repository URL. Use format: owner/repo-name", err=True)
        return
    
    api = RepoRougeAPI(config['server_url'], config['token'])
    
    try:
        # Get repository info first
        repo_info = api.get_repo_info(owner, repo_name)
        
        # Clone repository
        zip_data = api.clone_repo(owner, repo_name, branch)
        
        # Determine target directory
        target_dir = Path(directory) if directory else Path(repo_name)
        
        if target_dir.exists():
            if not click.confirm(f"Directory '{target_dir}' already exists. Overwrite?"):
                return
            shutil.rmtree(str(target_dir))
        
        # Extract ZIP
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(zip_data)
            tmp_file.flush()
            
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                zip_ref.extractall(str(target_dir))
        
        os.unlink(tmp_file.name)
        
        # Create local repository configuration
        repo_config_dir = target_dir / ".reporouge"
        repo_config_dir.mkdir(parents=True, exist_ok=True)
        
        local_config = {
            "owner": owner,
            "repo_name": repo_name,
            "current_branch": branch,
            "cloned_at": datetime.now().isoformat()
        }
        
        config_file_path = repo_config_dir / "config.json"
        with open(str(config_file_path), 'w', encoding='utf-8') as f:
            json.dump(local_config, f, indent=2)
        
        click.echo(f"✅ Successfully cloned {repo_url} to {target_dir}")
        click.echo(f"📁 Branch: {branch}")
        click.echo(f"📝 Description: {repo_info.get('description', 'No description')}")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Clone failed: {e}", err=True)

@cli.command()
@click.pass_context
def status(ctx):
    """Show repository status"""
    config_manager = ctx.obj['config']
    repo_config = config_manager.get_local_repo_config()
    
    if not repo_config:
        click.echo("❌ Not in a RepoRouge repository", err=True)
        return
    
    click.echo(f"Repository: {repo_config['owner']}/{repo_config['repo_name']}")
    click.echo(f"Current branch: {repo_config['current_branch']}")
    click.echo(f"Cloned at: {repo_config['cloned_at']}")
    
    # Show modified files (basic implementation)
    click.echo("Modified files:")
    try:
        for root, dirs, files in os.walk('.'):
            # Skip .reporouge directory
            if '.reporouge' in root:
                continue
            for file in files:
                file_path = Path(root) / file
                try:
                    relative_path = file_path.relative_to('.')
                    click.echo(f"  M {relative_path}")
                except ValueError:
                    # Skip files that can't be made relative
                    continue
    except Exception:
        click.echo("  Unable to scan for modified files")

@cli.command()
@click.option('--all', '-a', is_flag=True, help='Show all branches')
@click.pass_context
def branch(ctx, all: bool):
    """List branches or show current branch"""
    config_manager = ctx.obj['config']
    repo_config = config_manager.get_local_repo_config()
    config = config_manager.load_config()
    
    if not repo_config or not config.get('token'):
        click.echo("❌ Not in a RepoRouge repository or not logged in", err=True)
        return
    
    api = RepoRougeAPI(config['server_url'], config['token'])
    
    try:
        branches_info = api.get_branches(repo_config['owner'], repo_config['repo_name'])
        current_branch = branches_info['current_branch']
        
        if all:
            click.echo("All branches:")
            for branch_info in branches_info['branches']:
                marker = "* " if branch_info['name'] == current_branch else "  "
                click.echo(f"{marker}{branch_info['name']}")
        else:
            click.echo(f"Current branch: {current_branch}")
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Failed to get branches: {e}", err=True)

@cli.command()
@click.argument('branch_name')
@click.pass_context
def checkout(ctx, branch_name: str):
    """Switch to a different branch"""
    config_manager = ctx.obj['config']
    repo_config = config_manager.get_local_repo_config()
    config = config_manager.load_config()
    
    if not repo_config or not config.get('token'):
        click.echo("❌ Not in a RepoRouge repository or not logged in", err=True)
        return
    
    api = RepoRougeAPI(config['server_url'], config['token'])
    
    try:
        # Switch branch on server
        result = api.switch_branch(repo_config['owner'], repo_config['repo_name'], branch_name)
        
        # Update local config
        repo_config['current_branch'] = branch_name
        config_path = Path('.reporouge') / 'config.json'
        with open(str(config_path), 'w', encoding='utf-8') as f:
            json.dump(repo_config, f, indent=2)
        
        # Re-clone the branch content
        zip_data = api.clone_repo(repo_config['owner'], repo_config['repo_name'], branch_name)
        
        # Clear current directory (except .reporouge)
        for item in Path('.').iterdir():
            if item.name != '.reporouge':
                if item.is_dir():
                    shutil.rmtree(str(item))
                else:
                    item.unlink()
        
        # Extract new branch content
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(zip_data)
            tmp_file.flush()
            
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if not member.startswith('.reporouge/'):
                        zip_ref.extract(member, '.')
        
        os.unlink(tmp_file.name)
        
        click.echo(f"✅ Switched to branch '{branch_name}'")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Checkout failed: {e}", err=True)

@cli.command()
@click.option('--message', '-m', prompt=True, help='Commit message')
@click.pass_context
def push(ctx, message: str):
    """Push changes to the repository"""
    config_manager = ctx.obj['config']
    repo_config = config_manager.get_local_repo_config()
    config = config_manager.load_config()
    
    if not repo_config or not config.get('token'):
        click.echo("❌ Not in a RepoRouge repository or not logged in", err=True)
        return
    
    api = RepoRougeAPI(config['server_url'], config['token'])
    
    # Collect all files
    files_to_push = []
    try:
        for root, dirs, files in os.walk('.'):
            # Skip .reporouge directory
            if '.reporouge' in root:
                continue
            
            for file in files:
                file_path = Path(root) / file
                try:
                    relative_path = str(file_path.relative_to('.'))
                    
                    with open(str(file_path), 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    files_to_push.append({
                        "path": relative_path,
                        "content": content,
                        "message": message
                    })
                except (UnicodeDecodeError, PermissionError, ValueError):
                    # Skip binary files, files we can't read, or files with path issues
                    continue
    except Exception as e:
        click.echo(f"❌ Error scanning files: {e}", err=True)
        return
    
    if not files_to_push:
        click.echo("No files to push")
        return
    
    try:
        result = api.push_files(
            repo_config['owner'], 
            repo_config['repo_name'], 
            files_to_push, 
            repo_config['current_branch']
        )
        
        click.echo(f"✅ Successfully pushed {result['files']} files")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Push failed: {e}", err=True)

@cli.command()
@click.pass_context
def pull(ctx):
    """Pull latest changes from the repository"""
    config_manager = ctx.obj['config']
    repo_config = config_manager.get_local_repo_config()
    config = config_manager.load_config()
    
    if not repo_config or not config.get('token'):
        click.echo("❌ Not in a RepoRouge repository or not logged in", err=True)
        return
    
    api = RepoRougeAPI(config['server_url'], config['token'])
    
    try:
        # Clone the current branch
        zip_data = api.clone_repo(
            repo_config['owner'], 
            repo_config['repo_name'], 
            repo_config['current_branch']
        )
        
        # Clear current directory (except .reporouge)
        for item in Path('.').iterdir():
            if item.name != '.reporouge':
                if item.is_dir():
                    shutil.rmtree(str(item))
                else:
                    item.unlink()
        
        # Extract new content
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(zip_data)
            tmp_file.flush()
            
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if not member.startswith('.reporouge/'):
                        zip_ref.extract(member, '.')
        
        os.unlink(tmp_file.name)
        
        click.echo("✅ Successfully pulled latest changes")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Pull failed: {e}", err=True)

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ An unexpected error occurred: {e}", err=True)
        click.echo("Please report this issue if it persists.", err=True)
        sys.exit(1)
