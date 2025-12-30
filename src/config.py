"""
Configuration management for the book search system
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from src.logger import setup_logger

logger = setup_logger(__name__)


class ConfigManager:
    """Manages config.yaml file loading and updating"""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            self.config_path = Path(__file__).parent.parent / "config.yaml"
        else:
            self.config_path = config_path

    def load_config(self) -> Dict:
        """Load and parse config.yaml file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {}
        except FileNotFoundError:
            logger.warning(f"config.yaml file not found: {self.config_path}")
            return {'sources': [], 'app_settings': {}}
        except yaml.YAMLError as e:
            logger.warning(f"config.yaml parsing error: {e}")
            return {'sources': [], 'app_settings': {}}

    def get_enabled_sources_by_priority(self, config: Optional[Dict] = None) -> List[Dict]:
        """Get enabled sources sorted by priority"""
        if config is None:
            config = self.load_config()

        sources = config.get('sources', [])
        enabled_sources = [s for s in sources if s.get('enabled', False)]
        return sorted(enabled_sources, key=lambda x: x.get('priority', 999))
