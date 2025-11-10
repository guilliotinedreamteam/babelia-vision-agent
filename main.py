#!/usr/bin/env python3
"""
Babelia Vision Agent - Main Entry Point

Autonomous AI agent that searches the Library of Babel's Babelia image archives
for meaningful, breakthrough imagery.
"""

import os
import sys
import asyncio
import signal
import logging
from pathlib import Path
import click
from dotenv import load_dotenv

from babelia_agent import BabeliaAgent
from babelia_agent.utils import setup_logging, load_config

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

# Global agent instance for signal handling
agent_instance = None


def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM"""
    logger.info("\n\nReceived shutdown signal. Saving progress...")
    if agent_instance:
        agent_instance.stop()
    sys.exit(0)


@click.command()
@click.option(
    '--max-images',
    default=None,
    type=int,
    help='Maximum number of images to analyze (default: unlimited)'
)
@click.option(
    '--threshold',
    default=None,
    type=float,
    help='Significance threshold (0.0-1.0, default from config)'
)
@click.option(
    '--sampling',
    type=click.Choice(['random', 'sequential']),
    default=None,
    help='Sampling strategy (default from config)'
)
@click.option(
    '--email',
    default=None,
    help='Override alert email address'
)
@click.option(
    '--test',
    is_flag=True,
    help='Test mode: analyze sample images without crawling'
)
def main(max_images, threshold, sampling, email, test):
    """
    Babelia Vision Agent - Autonomous Image Discovery
    
    Searches the infinite Library of Babel image archives for meaningful imagery
    using state-of-the-art AI and deep learning.
    """
    global agent_instance
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load configuration
    config = load_config()
    
    # Override config with CLI arguments
    if max_images:
        config['max_images'] = max_images
    if threshold:
        config['significance_threshold'] = threshold
    if sampling:
        config['sampling_mode'] = sampling
    if email:
        config['alert_email'] = email
    
    # Display banner
    print_banner()
    
    # Initialize agent
    logger.info("Initializing Babelia Vision Agent...")
    try:
        agent_instance = BabeliaAgent(config)
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Run test mode or start search
    try:
        if test:
            logger.info("Running in TEST mode...")
            agent_instance.run_tests()
        else:
            logger.info("Starting autonomous search...")
            logger.info(f"Configuration:")
            logger.info(f"  - Max images: {config.get('max_images', 'unlimited')}")
            logger.info(f"  - Threshold: {config['significance_threshold']}")
            logger.info(f"  - Sampling: {config['sampling_mode']}")
            logger.info(f"  - Alert email: {config['alert_email']}")
            logger.info("")
            
            # Start the search
            agent_instance.start_search()
            
    except KeyboardInterrupt:
        logger.info("\nSearch interrupted by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if agent_instance:
            agent_instance.cleanup()
    
    logger.info("Babelia Vision Agent terminated.")


def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           BABELIA VISION AGENT v1.0                          ║
    ║                                                              ║
    ║     Autonomous AI Discovery in the Library of Babel          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Searching infinite algorithmic space for meaningful imagery...
    
    """
    print(banner)


if __name__ == "__main__":
    main()