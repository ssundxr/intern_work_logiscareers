"""
Environment Variable Loading

Loads environment variables from .env file if present.
Provides foundation for typed configuration access.
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_file: Optional[str] = None) -> None:
    """
    Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file. If None, looks in current directory.
    """
    if env_file is None:
        # Look for .env in project root
        current_dir = Path(__file__).parent.parent
        env_file = current_dir / ".env"
    else:
        env_file = Path(env_file)
    
    if not env_file.exists():
        # .env file is optional
        return
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value


# Auto-load on import
load_env_file()
