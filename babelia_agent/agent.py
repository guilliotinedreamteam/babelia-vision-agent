"""
Main Agent Controller

Coordinates all components of the Babelia Vision Agent.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from babelia_agent.crawler import BabeliaCrawler
from babelia_agent.analyzer import ImageAnalyzer
from babelia_agent.notifier import EmailNotifier
from babelia_agent.storage import StorageManager

logger = logging.getLogger(__name__)


class BabeliaAgent:
    """Main agent controller that coordinates all components"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Babelia Vision Agent
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.running = False
        
        # Initialize components
        logger.info("Initializing components...")
        
        self.crawler = BabeliaCrawler(
            rate_limit=config.get('babelia_rate_limit', 2),
            sampling_mode=config.get('sampling_mode', 'random')
        )
        
        self.analyzer = ImageAnalyzer(
            model_name=config.get('clip_model', 'ViT-B/32'),
            significance_threshold=config.get('significance_threshold', 0.75),
            anomaly_threshold=config.get('anomaly_threshold', 0.85)
        )
        
        self.notifier = EmailNotifier(
            smtp_server=config.get('smtp_server'),
            smtp_port=config.get('smtp_port'),
            username=config.get('smtp_username'),
            password=config.get('smtp_password'),
            alert_email=config.get('alert_email')
        )
        
        self.storage = StorageManager(
            save_dir=config.get('image_save_dir', './discoveries'),
            db_path=config.get('database_path', './babelia_discoveries.db')
        )
        
        # Statistics
        self.stats = {
            'images_analyzed': 0,
            'discoveries': 0,
            'alerts_sent': 0,
            'start_time': None,
            'errors': 0
        }
        
        logger.info("Agent initialized successfully")
    
    def start_search(self, max_images: Optional[int] = None):
        """
        Start autonomous search for significant images
        
        Args:
            max_images: Maximum number of images to analyze (None = unlimited)
        """
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        max_images = max_images or self.config.get('max_images_per_run')
        
        logger.info(f"Starting search (max: {max_images or 'unlimited'})")
        
        while self.running:
            try:
                # Check if we've hit the limit
                if max_images and self.stats['images_analyzed'] >= max_images:
                    logger.info(f"Reached maximum images ({max_images})")
                    break
                
                # Fetch next image from Babelia
                image_data = self.crawler.fetch_next_image()
                
                if not image_data:
                    logger.warning("Failed to fetch image, retrying...")
                    time.sleep(5)
                    continue
                
                self.stats['images_analyzed'] += 1
                
                # Analyze image
                analysis_result = self.analyzer.analyze(image_data['image'])
                
                # Log progress every 100 images
                if self.stats['images_analyzed'] % 100 == 0:
                    self._log_progress()
                
                # Check if image is significant
                if analysis_result['is_significant']:
                    logger.info(f"\n🎯 SIGNIFICANT IMAGE FOUND! Score: {analysis_result['score']:.3f}")
                    self._handle_discovery(image_data, analysis_result)
                
            except KeyboardInterrupt:
                logger.info("\nSearch interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in search loop: {e}", exc_info=True)
                self.stats['errors'] += 1
                time.sleep(2)
        
        self._log_final_stats()
    
    def _handle_discovery(self, image_data: Dict, analysis_result: Dict):
        """
        Handle a significant image discovery
        
        Args:
            image_data: Image data from crawler
            analysis_result: Analysis results from analyzer
        """
        try:
            self.stats['discoveries'] += 1
            
            # Save image and metadata
            saved_path = self.storage.save_discovery(
                image=image_data['image'],
                score=analysis_result['score'],
                analysis=analysis_result,
                coordinates=image_data['coordinates']
            )
            
            logger.info(f"Image saved to: {saved_path}")
            
            # Send email alert
            if self.config.get('alert_email'):
                self.notifier.send_alert(
                    image_path=saved_path,
                    analysis=analysis_result,
                    coordinates=image_data['coordinates'],
                    stats=self.stats
                )
                self.stats['alerts_sent'] += 1
                logger.info("Email alert sent")
            
        except Exception as e:
            logger.error(f"Error handling discovery: {e}", exc_info=True)
    
    def _log_progress(self):
        """Log current progress statistics"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['images_analyzed'] / elapsed if elapsed > 0 else 0
        
        logger.info(
            f"Progress: {self.stats['images_analyzed']} images analyzed | "
            f"{self.stats['discoveries']} discoveries | "
            f"{rate:.2f} img/sec | "
            f"{self.stats['errors']} errors"
        )
    
    def _log_final_stats(self):
        """Log final statistics"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("FINAL STATISTICS")
        logger.info("="*60)
        logger.info(f"Total images analyzed: {self.stats['images_analyzed']}")
        logger.info(f"Discoveries: {self.stats['discoveries']}")
        logger.info(f"Alerts sent: {self.stats['alerts_sent']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Runtime: {elapsed/3600:.2f} hours")
        logger.info(f"Average rate: {self.stats['images_analyzed']/elapsed:.2f} img/sec")
        
        if self.stats['discoveries'] > 0:
            logger.info(f"Discovery rate: {self.stats['discoveries']/self.stats['images_analyzed']*100:.4f}%")
        
        logger.info("="*60 + "\n")
    
    def run_tests(self):
        """Run test mode with sample images"""
        logger.info("Running test mode...")
        
        # Test analyzer initialization
        logger.info("Testing AI models...")
        test_result = self.analyzer.test_models()
        
        if test_result:
            logger.info("✓ AI models loaded successfully")
        else:
            logger.error("✗ AI model test failed")
            return
        
        # Test email
        if self.config.get('alert_email'):
            logger.info("Testing email notifications...")
            try:
                self.notifier.send_test_email()
                logger.info("✓ Test email sent successfully")
            except Exception as e:
                logger.error(f"✗ Email test failed: {e}")
        
        logger.info("Test mode completed")
    
    def stop(self):
        """Stop the agent gracefully"""
        logger.info("Stopping agent...")
        self.running = False
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        self.storage.close()