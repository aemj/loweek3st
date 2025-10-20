"""
Configuration management for the Youtube Assistant application.
Supports multiple secure configuration methods.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class Config:
    """Application configuration with multiple secure loading methods."""
    
    def __init__(self):
        """Initialize configuration from the most secure available source."""
        self._config_data = self._load_configuration()
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from multiple sources in order of preference."""
        
        # Method 1: Try system environment variables first (most secure)
        if self._has_required_env_vars():
            print("✅ Loading from system environment variables")
            return self._load_from_env()
        
        # Method 2: Try external config file (outside project)
        external_config = Path.home() / ".config" / "youtube-assistant" / "config.json"
        if external_config.exists():
            print(f"✅ Loading from external config: {external_config}")
            return self._load_from_json(external_config)
        
        # Method 3: Try .env file (least secure, but fallback)
        if Path(".env").exists():
            print("⚠️  Loading from .env file (consider using more secure method)")
            load_dotenv()
            return self._load_from_env()
        
        # Method 4: Use defaults with warnings
        print("❌ No configuration found, using defaults")
        return self._get_defaults()
    
    def _has_required_env_vars(self) -> bool:
        """Check if required environment variables are set in system."""
        return bool(os.environ.get("OPENAI_API_KEY") and os.environ.get("VECTOR_STORE_ID"))
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # Required API Keys
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "VECTOR_STORE_ID": os.getenv("VECTOR_STORE_ID", ""),
            "MCP_URL": os.getenv("MCP_URL", ""),
            
            # Application Settings
            "APP_TITLE": os.getenv("APP_TITLE", "Youtube Assistant"),
            "APP_ICON": os.getenv("APP_ICON", "🎥"),
            
            # Default UI Settings
            "MAX_RESULTS_DEFAULT": int(os.getenv("MAX_RESULTS_DEFAULT", "3")),
            "ENABLE_WEB_SEARCH_DEFAULT": os.getenv("ENABLE_WEB_SEARCH_DEFAULT", "true").lower() == "true",
            "ENABLE_DOCUMENT_SEARCH_DEFAULT": os.getenv("ENABLE_DOCUMENT_SEARCH_DEFAULT", "false").lower() == "true",
            "ENABLE_MCP_SEARCH_DEFAULT": os.getenv("ENABLE_MCP_SEARCH_DEFAULT", "false").lower() == "true",

            # Agent Configuration
            "AGENT_NAME": os.getenv("AGENT_NAME", "Youtube Assistant"),
            "AGENT_INSTRUCTIONS": os.getenv("AGENT_INSTRUCTIONS", 
                "You are a research assistant who uses web search and document search to respond to questions."),
            "AGENT_MODEL": os.getenv("AGENT_MODEL", "gpt-4o-mini")
        }
    
    def _load_from_json(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            defaults = self._get_defaults()
            defaults.update(config)
            return defaults
        except Exception as e:
            print(f"❌ Error loading config from {config_path}: {e}")
            return self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "OPENAI_API_KEY": "",
            "VECTOR_STORE_ID": "",
            "MCP_URL": "",
            "APP_TITLE": "Youtube Assistant",
            "APP_ICON": "🎥",
            "MAX_RESULTS_DEFAULT": 3,
            "ENABLE_WEB_SEARCH_DEFAULT": True,
            "ENABLE_DOCUMENT_SEARCH_DEFAULT": False,
            "ENABLE_MCP_SEARCH_DEFAULT": False,
            "AGENT_NAME": "Youtube Assistant",
            "AGENT_INSTRUCTIONS": "You are a research assistant who uses web search and document search to respond to questions.",
            "AGENT_MODEL": "gpt-4o-mini"
        }
    
    # Properties for easy access
    @property
    def OPENAI_API_KEY(self) -> str:
        return self._config_data.get("OPENAI_API_KEY", "")
    
    @property
    def VECTOR_STORE_ID(self) -> str:
        return self._config_data.get("VECTOR_STORE_ID", "")
    
    @property
    def MCP_URL(self) -> str:
        return self._config_data.get("MCP_URL", "")
    
    @property
    def APP_TITLE(self) -> str:
        return self._config_data.get("APP_TITLE", "Youtube Assistant")
    
    @property
    def APP_ICON(self) -> str:
        return self._config_data.get("APP_ICON", "🎥")
    
    @property
    def MAX_RESULTS_DEFAULT(self) -> int:
        return self._config_data.get("MAX_RESULTS_DEFAULT", 3)
    
    @property
    def ENABLE_WEB_SEARCH_DEFAULT(self) -> bool:
        return self._config_data.get("ENABLE_WEB_SEARCH_DEFAULT", True)
    
    @property
    def ENABLE_DOCUMENT_SEARCH_DEFAULT(self) -> bool:
        return self._config_data.get("ENABLE_DOCUMENT_SEARCH_DEFAULT", True)
    
    @property
    def ENABLE_MCP_SEARCH_DEFAULT(self) -> bool:
        return self._config_data.get("ENABLE_MCP_SEARCH_DEFAULT", False)
    
    @property
    def AGENT_NAME(self) -> str:
        return self._config_data.get("AGENT_NAME", "Youtube Assistant")
    
    @property
    def AGENT_INSTRUCTIONS(self) -> str:
        return self._config_data.get("AGENT_INSTRUCTIONS", 
            "You are a research assistant who uses web search and document search to respond to questions.")
    
    @property
    def AGENT_MODEL(self) -> str:
        return self._config_data.get("AGENT_MODEL", "gpt-4o-mini")
    
    @classmethod
    def validate_required_keys(cls) -> tuple[bool, list[str]]:
        """
        Validate that core required environment variables are set.
        Note: Only validates truly required keys, not optional ones like MCP_URL.
        
        Returns:
            tuple: (is_valid, missing_keys)
        """
        config_instance = cls()
        missing_keys = []
        
        if not config_instance.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        
        # Note: VECTOR_STORE_ID and MCP_URL are optional - only required when their respective features are enabled
        
        return len(missing_keys) == 0, missing_keys
    
    @classmethod
    def get_env_status(cls) -> dict:
        """Get the status of environment variables."""
        config_instance = cls()
        is_valid, missing_keys = cls.validate_required_keys()
        
        return {
            "is_valid": is_valid,
            "missing_keys": missing_keys,
            "openai_key_set": bool(config_instance.OPENAI_API_KEY),
            "vector_store_set": bool(config_instance.VECTOR_STORE_ID),
            "mcp_url_set": bool(config_instance.MCP_URL),
        }

# Create a global config instance
config = Config()
