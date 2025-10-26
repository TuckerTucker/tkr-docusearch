"""
Environment variable validation for DocuSearch.

Validates that required environment variables are set before application startup
to prevent runtime errors due to missing configuration.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EnvironmentValidationError(Exception):
    """Raised when required environment variables are missing or invalid."""


def validate_env_vars(
    required: Optional[List[str]] = None,
    optional: Optional[Dict[str, str]] = None,
    strict: bool = True,
) -> Dict[str, str]:
    """
    Validate required environment variables are set.

    Args:
        required: List of required environment variable names
        optional: Dict of optional variables with default values
        strict: If True, raise exception on missing required vars

    Returns:
        Dict of environment variables (required + optional with defaults)

    Raises:
        EnvironmentValidationError: If required variables are missing (when strict=True)

    Examples:
        >>> validate_env_vars(['OPENAI_API_KEY'], {'LOG_LEVEL': 'INFO'})
        {'OPENAI_API_KEY': 'sk-...', 'LOG_LEVEL': 'INFO'}
    """
    required = required or []
    optional = optional or {}
    env_vars = {}
    missing = []

    # Check required variables
    for var_name in required:
        value = os.getenv(var_name)
        if value:
            env_vars[var_name] = value
            logger.debug(f"✓ {var_name} is set")
        else:
            missing.append(var_name)
            logger.error(f"✗ {var_name} is NOT set (required)")

    # Add optional variables with defaults
    for var_name, default_value in optional.items():
        value = os.getenv(var_name, default_value)
        env_vars[var_name] = value
        if os.getenv(var_name):
            logger.debug(f"✓ {var_name} is set")
        else:
            logger.debug(f"○ {var_name} using default: {default_value}")

    # Handle missing required variables
    if missing:
        error_msg = (
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"\n"
            f"Please set these variables in your .env file:\n"
            f"  1. Copy .env.example to .env\n"
            f"  2. Edit .env and add your credentials\n"
            f"\n"
            f"See .env.example for all available configuration options."
        )

        if strict:
            raise EnvironmentValidationError(error_msg)
        else:
            logger.warning(error_msg)

    return env_vars


def validate_llm_provider() -> str:
    """
    Validate LLM provider configuration.

    Returns:
        Provider name (openai, anthropic, google, mlx)

    Raises:
        EnvironmentValidationError: If provider is invalid or API key is missing
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    valid_providers = {"openai", "anthropic", "google", "mlx"}

    if provider not in valid_providers:
        raise EnvironmentValidationError(
            f"Invalid LLM_PROVIDER: {provider}. " f"Must be one of: {', '.join(valid_providers)}"
        )

    # Validate API key for the selected provider
    api_key_mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "mlx": None,  # Local model, no API key needed
    }

    required_key = api_key_mapping[provider]
    if required_key and not os.getenv(required_key):
        raise EnvironmentValidationError(
            f"LLM_PROVIDER is set to '{provider}' but {required_key} is not set.\n"
            f"Get your API key from:\n"
            f"  OpenAI: https://platform.openai.com/api-keys\n"
            f"  Anthropic: https://console.anthropic.com/\n"
            f"  Google: https://makersuite.google.com/app/apikey"
        )

    logger.info(f"✓ LLM provider validated: {provider}")
    return provider


def validate_security_critical_vars() -> None:
    """
    Validate security-critical environment variables.

    Checks:
    - No placeholder values (e.g., "your-api-key-here")
    - No obviously fake values (e.g., "test", "dummy")
    - Reasonable key lengths

    Raises:
        EnvironmentValidationError: If security issues detected
    """
    security_vars: Dict[str, Dict[str, Any]] = {
        "OPENAI_API_KEY": {"min_length": 20, "prefix": "sk-"},
        "ANTHROPIC_API_KEY": {"min_length": 20, "prefix": None},
        "GOOGLE_API_KEY": {"min_length": 20, "prefix": None},
    }

    placeholder_values = {
        "your-openai-api-key-here",
        "your-anthropic-api-key-here",
        "your-google-api-key-here",
        "your-ngrok-authtoken-here",
        "test",
        "dummy",
        "fake",
        "placeholder",
    }

    for var_name, requirements in security_vars.items():
        value = os.getenv(var_name)
        if not value:
            continue  # Skip if not set (will be caught by other validation)

        # Check for placeholder values
        if value.lower() in placeholder_values:
            raise EnvironmentValidationError(
                f"{var_name} contains a placeholder value: '{value}'\n"
                f"Please replace with your actual API key from .env"
            )

        # Check minimum length
        if len(value) < requirements["min_length"]:
            logger.warning(
                f"{var_name} is unusually short ({len(value)} chars). "
                f"Expected at least {requirements['min_length']} characters."
            )

        # Check expected prefix
        if requirements["prefix"] and not value.startswith(requirements["prefix"]):
            logger.warning(
                f"{var_name} does not start with expected prefix '{requirements['prefix']}'"
            )

    logger.info("✓ Security-critical variables validated")


def validate_all(strict: bool = True) -> Dict[str, str]:
    """
    Validate all environment variables for DocuSearch.

    Args:
        strict: If True, raise exceptions on validation failures

    Returns:
        Dict of validated environment variables

    Raises:
        EnvironmentValidationError: If validation fails (when strict=True)
    """
    logger.info("Validating environment configuration...")

    # Core required variables
    required = [
        "CHROMA_HOST",
        "CHROMA_PORT",
    ]

    # Optional variables with defaults
    optional = {
        "LOG_LEVEL": "INFO",
        "WORKER_PORT": "8002",
        "RESEARCH_API_PORT": "8004",
        "DEVICE": "cpu",
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
        "ASR_ENABLED": "false",
        "LOCAL_PREPROCESS_ENABLED": "false",
    }

    # Validate basic variables
    env_vars = validate_env_vars(required, optional, strict=strict)

    # Validate LLM provider and API keys
    try:
        validate_llm_provider()
    except EnvironmentValidationError as e:
        if strict:
            raise
        else:
            logger.warning(f"LLM provider validation failed: {e}")

    # Validate security-critical variables
    try:
        validate_security_critical_vars()
    except EnvironmentValidationError as e:
        if strict:
            raise
        else:
            logger.warning(f"Security validation warning: {e}")

    logger.info("✓ Environment validation complete")
    return env_vars


def print_env_summary() -> None:
    """Print a summary of environment configuration (safe, no secrets)."""
    print("=" * 70)
    print("DocuSearch Environment Configuration")
    print("=" * 70)
    print(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'openai')}")
    print(f"LLM Model: {os.getenv('LLM_MODEL', 'gpt-4')}")
    print(f"ChromaDB: {os.getenv('CHROMA_HOST', 'localhost')}:{os.getenv('CHROMA_PORT', '8001')}")
    print(f"Worker Port: {os.getenv('WORKER_PORT', '8002')}")
    print(f"Research API Port: {os.getenv('RESEARCH_API_PORT', '8004')}")
    print(f"Device: {os.getenv('DEVICE', 'cpu')}")
    print(f"ASR Enabled: {os.getenv('ASR_ENABLED', 'false')}")
    print(f"Local Preprocess: {os.getenv('LOCAL_PREPROCESS_ENABLED', 'false')}")
    print(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")

    # Check API keys (don't print actual values)
    api_keys = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "Google": os.getenv("GOOGLE_API_KEY"),
        "Ngrok": os.getenv("NGROK_AUTHTOKEN"),
    }

    print("\nAPI Keys Status:")
    for name, value in api_keys.items():
        status = "✓ Set" if value else "✗ Not set"
        print(f"  {name}: {status}")

    print("=" * 70)


if __name__ == "__main__":
    # Allow standalone testing
    logging.basicConfig(level=logging.INFO)

    try:
        validate_all(strict=True)
        print_env_summary()
        print("\n✓ All environment variables are valid!")
        sys.exit(0)
    except EnvironmentValidationError as e:
        print(f"\n✗ Environment validation failed:\n{e}")
        sys.exit(1)
