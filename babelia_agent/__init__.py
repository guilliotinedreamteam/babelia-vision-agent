"""
Babelia Vision Agent

Autonomous AI system for discovering significant imagery in the Library of Babel.
"""

from babelia_agent.agent import BabeliaAgent
from babelia_agent.crawler import BabeliaCrawler
from babelia_agent.analyzer import ImageAnalyzer
from babelia_agent.notifier import EmailNotifier
from babelia_agent.storage import StorageManager

__version__ = "1.0.0"
__author__ = "guilliotinedreamteam"

__all__ = [
    "BabeliaAgent",
    "BabeliaCrawler",
    "ImageAnalyzer",
    "EmailNotifier",
    "StorageManager"
]