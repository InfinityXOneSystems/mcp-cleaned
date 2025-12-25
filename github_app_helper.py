"""
GitHub App Integration Helper
Implements Infinity XOS Orchestrator GitHub App
"""

import os
import json
import time
import jwt
import requests
from datetime import datetime, timedelta
from pathlib import Path

class GitHubApp:
    """GitHub App authentication and API helper"""
    
    def __init__(self):
        self.config = self._load_config()
        self.private_key = self._load_private_key()
        self.app_id = self.config.get('app_id', '2494652')
        self.installation_ids = {
            'personal': self.config.get('installation_id_personal'),
            'infinityxone': self.config.get('installation_id_infinityxone')
        }
        
    def _load_config(self):
        """Load GitHub App configuration"""
        config_path = Path.home() / 'AppData/Local/InfinityXOne/CredentialManager/.github-app-config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Fallback to inline config
        return {
            'app_id': '2494652',
            'client_id': 'Iv23liWSRKS3dsHX0oYV',
            'app_name': 'Infinity XOS Orchestrator',
            'organization': 'InfinityXOneSystems',
            'homepage': 'https://infinityxai.com',
            'callback_url': 'https://admin.infinityxai.com/auth/github/callback',
            'webhook_url': 'https://admin.infinityxai.com/webhooks/github',
            'setup_url': 'https://infinityxai.com/admin',
            'public_link': 'https://github.com/apps/infinity-xos-orchestrator'
        }
    
    def _load_private_key(self):
        """Load GitHub App private key"""
        key_path = Path.home() / 'AppData/Local/InfinityXOne/CredentialManager/github-app-private-key.pem'
        if key_path.exists():
            with open(key_path, 'r') as f:
                return f.read()
        return None
    
    def generate_jwt(self):
        """Generate JWT for GitHub App authentication"""
        if not self.private_key:
            raise ValueError("GitHub App private key not found")
        
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + (10 * 60),  # 10 minutes
            'iss': self.app_id
        }
        
        token = jwt.encode(payload, self.private_key, algorithm='RS256')
        return token
    
    def get_installation_token(self, installation_type='infinityxone'):
        """Get installation access token for a specific installation"""
        installation_id = self.installation_ids.get(installation_type)
        if not installation_id:
            raise ValueError(f"Installation ID not found for type: {installation_type}")
        
        jwt_token = self.generate_jwt()
        url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data['token']
    
    def make_api_request(self, method, endpoint, installation_type='infinityxone', **kwargs):
        """Make authenticated API request using installation token"""
        token = self.get_installation_token(installation_type)
        headers = kwargs.pop('headers', {})
        headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
        
        url = f'https://api.github.com{endpoint}'
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        return response.json() if response.text else None
    
    def list_repos(self, installation_type='infinityxone'):
        """List repositories accessible to the installation"""
        return self.make_api_request('GET', '/installation/repositories', installation_type)
    
    def get_repo(self, owner, repo, installation_type='infinityxone'):
        """Get repository details"""
        return self.make_api_request('GET', f'/repos/{owner}/{repo}', installation_type)
    
    def create_issue(self, owner, repo, title, body=None, labels=None, installation_type='infinityxone'):
        """Create an issue in a repository"""
        data = {'title': title}
        if body:
            data['body'] = body
        if labels:
            data['labels'] = labels
        
        return self.make_api_request(
            'POST', 
            f'/repos/{owner}/{repo}/issues',
            installation_type,
            json=data
        )
    
    def get_file_content(self, owner, repo, path, ref='main', installation_type='infinityxone'):
        """Get file content from repository"""
        endpoint = f'/repos/{owner}/{repo}/contents/{path}'
        if ref:
            endpoint += f'?ref={ref}'
        return self.make_api_request('GET', endpoint, installation_type)
    
    def list_organization_repos(self):
        """List all repositories in the organization"""
        org = self.config.get('organization', 'InfinityXOneSystems')
        return self.make_api_request('GET', f'/orgs/{org}/repos', 'infinityxone')
    
    def get_rate_limit(self, installation_type='infinityxone'):
        """Check API rate limit status"""
        return self.make_api_request('GET', '/rate_limit', installation_type)


def test_github_app():
    """Test GitHub App integration"""
    print("\n🔍 Testing GitHub App Integration...")
    
    try:
        app = GitHubApp()
        print(f"✓ GitHub App initialized")
        print(f"  • App ID: {app.app_id}")
        print(f"  • App Name: {app.config.get('app_name')}")
        print(f"  • Organization: {app.config.get('organization')}")
        
        # Generate JWT
        jwt_token = app.generate_jwt()
        print(f"\n✓ JWT generated (expires in 10 minutes)")
        
        # Get installation token
        token = app.get_installation_token('infinityxone')
        print(f"✓ Installation token obtained")
        
        # Check rate limit
        rate_limit = app.get_rate_limit('infinityxone')
        print(f"\n📊 Rate Limit Status:")
        print(f"  • Remaining: {rate_limit['rate']['remaining']}/{rate_limit['rate']['limit']}")
        print(f"  • Resets at: {datetime.fromtimestamp(rate_limit['rate']['reset'])}")
        
        # List repos
        repos = app.list_organization_repos()
        print(f"\n📦 Organization Repositories ({repos['total_count']} total):")
        for repo in repos['repositories'][:5]:
            print(f"  • {repo['full_name']}")
        
        print("\n✅ GitHub App integration is fully operational!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_github_app()
