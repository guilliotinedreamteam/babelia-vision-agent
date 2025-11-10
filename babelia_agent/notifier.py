"""
Email Notifier

Sends email alerts when significant images are discovered.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sends email alerts for significant discoveries"""
    
    def __init__(self, smtp_server: str, smtp_port: int,
                 username: str, password: str, alert_email: str):
        """
        Initialize email notifier
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            alert_email: Email address to send alerts to
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.alert_email = alert_email
        
        logger.info(f"Email notifier initialized (server: {smtp_server})")
    
    def send_alert(self, image_path: str, analysis: Dict[str, Any],
                   coordinates: Dict[str, str], stats: Dict[str, int]):
        """
        Send email alert for significant discovery
        
        Args:
            image_path: Path to saved image
            analysis: Analysis results
            coordinates: Babelia coordinates
            stats: Agent statistics
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = self.alert_email
            msg['Subject'] = f"🔍 Babelia Discovery Alert - Score: {analysis['score']:.3f}"
            
            # Create email body
            body = self._create_email_body(analysis, coordinates, stats)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach image
            with open(image_path, 'rb') as f:
                img_data = f.read()
                image = MIMEImage(img_data, name=Path(image_path).name)
                msg.attach(image)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {self.alert_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            raise
    
    def _create_email_body(self, analysis: Dict, coordinates: Dict,
                          stats: Dict) -> str:
        """
        Create HTML email body
        """
        top_matches = analysis['details']['top_matches']
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="margin: 0;">🔍 Significant Image Discovered!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Babelia Vision Agent</p>
            </div>
            
            <div style="padding: 20px; background-color: #f5f5f5; margin-top: 20px; border-radius: 10px;">
                <h2 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                    Analysis Results
                </h2>
                
                <table style="width: 100%; margin-top: 15px;">
                    <tr>
                        <td style="padding: 8px; background-color: white; border-radius: 5px; margin-bottom: 5px;">
                            <strong>Significance Score:</strong>
                        </td>
                        <td style="padding: 8px; background-color: white; border-radius: 5px; text-align: right;">
                            <span style="background-color: #667eea; color: white; padding: 5px 15px; 
                                       border-radius: 20px; font-weight: bold;">
                                {analysis['score']:.3f}
                            </span>
                        </td>
                    </tr>
                    <tr><td colspan="2" style="height: 10px;"></td></tr>
                    <tr>
                        <td style="padding: 8px; background-color: white; border-radius: 5px;">
                            <strong>Primary Match:</strong>
                        </td>
                        <td style="padding: 8px; background-color: white; border-radius: 5px; text-align: right;">
                            {analysis['reason']}
                        </td>
                    </tr>
                </table>
                
                <h3 style="color: #667eea; margin-top: 20px;">Top Semantic Matches:</h3>
                <ol style="background-color: white; padding: 20px; border-radius: 5px;">
        """
        
        for prompt, score in top_matches:
            body += f"<li><strong>{prompt}</strong>: {score:.3f}</li>"
        
        body += f"""
                </ol>
                
                <h3 style="color: #667eea; margin-top: 20px;">Babelia Coordinates:</h3>
                <div style="background-color: #2d3748; color: #68d391; padding: 15px; 
                           border-radius: 5px; font-family: monospace; overflow-x: auto;">
                    <strong>Hex:</strong> {coordinates['hex_name']}<br>
                    <strong>Wall:</strong> {coordinates['wall']} | 
                    <strong>Shelf:</strong> {coordinates['shelf']} | 
                    <strong>Volume:</strong> {coordinates['volume']} | 
                    <strong>Page:</strong> {coordinates['page']}
                </div>
                
                <h3 style="color: #667eea; margin-top: 20px;">Search Statistics:</h3>
                <table style="width: 100%; background-color: white; padding: 15px; border-radius: 5px;">
                    <tr>
                        <td style="padding: 5px;"><strong>Images Analyzed:</strong></td>
                        <td style="text-align: right;">{stats['images_analyzed']:,}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Total Discoveries:</strong></td>
                        <td style="text-align: right;">{stats['discoveries']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Discovery Rate:</strong></td>
                        <td style="text-align: right;">
                            {stats['discoveries']/stats['images_analyzed']*100:.4f}%
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #718096; font-size: 12px;">
                <p>Generated by Babelia Vision Agent</p>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """
        
        return body
    
    def send_test_email(self):
        """Send a test email to verify configuration"""
        try:
            msg = MIMEText("This is a test email from Babelia Vision Agent.")
            msg['From'] = self.username
            msg['To'] = self.alert_email
            msg['Subject'] = "Test Email - Babelia Vision Agent"
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info("Test email sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            raise