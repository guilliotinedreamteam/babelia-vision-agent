"""
Utility Functions
"""

import os
import logging
import coloredlogs
from typing import Dict, Any
from pathlib import Path


def setup_logging(log_level: str = None) -> logging.Logger:
    """
    Setup application logging
    
    Args:
        log_level: Logging level (default from env or INFO)
    
    Returns:
        Logger instance
    """
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    
    # Create logs directory
    Path('./logs').mkdir(exist_ok=True)
    
    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Console handler with colors
    coloredlogs.install(
        level=log_level,
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level_styles={
            'debug': {'color': 'green'},
            'info': {'color': 'cyan'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red'},
            'critical': {'color': 'red', 'bold': True}
        }
    )
    
    # File handler
    file_handler = logging.FileHandler('./logs/babelia_agent.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables
    
    Returns:
        Configuration dictionary
    """
    config = {
        # Email settings
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'smtp_username': os.getenv('SMTP_USERNAME', ''),
        'smtp_password': os.getenv('SMTP_PASSWORD', ''),
        'alert_email': os.getenv('ALERT_EMAIL', 'donavanpyle@gmail.com'),
        
        # AI model settings
        'clip_model': os.getenv('CLIP_MODEL', 'ViT-B/32'),
        'significance_threshold': float(os.getenv('SIGNIFICANCE_THRESHOLD', 0.75)),
        'anomaly_threshold': float(os.getenv('ANOMALY_THRESHOLD', 0.85)),
        
        # Crawler settings
        'max_images_per_run': int(os.getenv('MAX_IMAGES_PER_RUN', 1000)) 
                             if os.getenv('MAX_IMAGES_PER_RUN') else None,
        'babelia_rate_limit': float(os.getenv('BABELIA_RATE_LIMIT', 2.0)),
        'sampling_mode': os.getenv('SAMPLING_MODE', 'random'),
        
        # Storage settings
        'image_save_dir': os.getenv('IMAGE_SAVE_DIR', './discoveries'),
        'database_path': os.getenv('DATABASE_PATH', './babelia_discoveries.db'),
    }
    
    # Validate required settings
    if not config['smtp_username'] or not config['smtp_password']:
        logging.warning("Email credentials not configured - alerts will be disabled")
    
    return config