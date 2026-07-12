import logging

import yaml
from pydantic import ValidationError

from app.core.config import get_settings
from app.models.university import UniversityConfig

logger = logging.getLogger(__name__)

_registry: dict[str, UniversityConfig] = {}

def load_universities() -> None:
    """Scan the universities directory and load configuration files.
    
    Raises:
        ValueError: If a configuration file is invalid or the slug does not
            match the folder name.
    """
    settings = get_settings()
    universities_dir = settings.universities_dir

    if not universities_dir.exists() or not universities_dir.is_dir():
        logger.warning(f"Universities directory not found at {universities_dir}")
        return

    _registry.clear()

    for path in universities_dir.iterdir():
        if not path.is_dir():
            continue

        config_file = path / "config.yaml"
        if not config_file.exists():
            continue

        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                raise ValueError(f"Config must be a YAML dictionary, got {type(data)}")

            config = UniversityConfig(**data)

            if config.slug != path.name:
                raise ValueError(
                    f"Slug '{config.slug}' does not match folder name '{path.name}'"
                )
            
            _registry[config.slug] = config
            logger.info(f"Loaded configuration for university: {config.name} ({config.slug})")
            
        except ValidationError as e:
            raise ValueError(f"Invalid configuration in {config_file}:\n{e}") from e
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_file}:\n{e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load {config_file}: {e}") from e

def get_university(slug: str) -> UniversityConfig:
    """Get a university configuration by its slug.
    
    Raises:
        KeyError: If the university is not found.
    """
    try:
        return _registry[slug]
    except KeyError as e:
        raise KeyError(f"University with slug '{slug}' not found.") from e

def list_universities() -> list[UniversityConfig]:
    """Get a list of all loaded university configurations."""
    return list(_registry.values())
