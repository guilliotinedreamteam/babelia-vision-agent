"""
Image Analyzer

Uses CLIP and other AI models to detect significant imagery.
"""

import logging
import torch
import numpy as np
from typing import Dict, Any, List
from PIL import Image
import open_clip
from scipy import stats

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """AI-powered image analysis using CLIP and anomaly detection"""
    
    # Evaluation prompts for CLIP
    SIGNIFICANCE_PROMPTS = [
        "a photograph of a human face",
        "a photograph of a person",
        "a clear recognizable object",
        "readable text or writing",
        "a scientific diagram or chart",
        "a map or schematic",
        "an artistic composition",
        "a photograph of an animal",
        "a photograph of a building or structure",
        "a photograph of a vehicle",
        "a historical document",
        "shocking or disturbing imagery",
        "a clear meaningful image"
    ]
    
    NOISE_PROMPTS = [
        "random noise",
        "static",
        "pure randomness",
        "meaningless pixels",
        "visual noise"
    ]
    
    def __init__(self, model_name: str = 'ViT-B-32', 
                 significance_threshold: float = 0.75,
                 anomaly_threshold: float = 0.85):
        """
        Initialize analyzer
        
        Args:
            model_name: CLIP model name
            significance_threshold: Threshold for significance score
            anomaly_threshold: Threshold for anomaly detection
        """
        self.significance_threshold = significance_threshold
        self.anomaly_threshold = anomaly_threshold
        
        logger.info(f"Loading CLIP model: {model_name}...")
        
        # Load CLIP model
        try:
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name, pretrained='openai'
            )
            self.tokenizer = open_clip.get_tokenizer(model_name)
            
            # Use GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"CLIP model loaded successfully (device: {self.device})")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
        
        # Pre-encode text prompts
        self._encode_prompts()
    
    def _encode_prompts(self):
        """Pre-encode text prompts for efficiency"""
        with torch.no_grad():
            # Encode significance prompts
            sig_tokens = self.tokenizer(self.SIGNIFICANCE_PROMPTS)
            self.sig_features = self.model.encode_text(sig_tokens.to(self.device))
            self.sig_features /= self.sig_features.norm(dim=-1, keepdim=True)
            
            # Encode noise prompts
            noise_tokens = self.tokenizer(self.NOISE_PROMPTS)
            self.noise_features = self.model.encode_text(noise_tokens.to(self.device))
            self.noise_features /= self.noise_features.norm(dim=-1, keepdim=True)
    
    def analyze(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze image for significance
        
        Args:
            image: PIL Image
        
        Returns:
            Dictionary with analysis results
        """
        # Stage 1: Noise detection
        is_noise, noise_score = self._detect_noise(image)
        
        if is_noise:
            return {
                'is_significant': False,
                'score': 0.0,
                'reason': 'pure_noise',
                'noise_score': noise_score,
                'details': {}
            }
        
        # Stage 2: CLIP semantic analysis
        clip_results = self._clip_analysis(image)
        
        # Stage 3: Calculate final significance score
        final_score = self._calculate_significance_score(clip_results, noise_score)
        
        is_significant = final_score >= self.significance_threshold
        
        return {
            'is_significant': is_significant,
            'score': final_score,
            'reason': clip_results['top_match'] if is_significant else 'below_threshold',
            'noise_score': noise_score,
            'details': {
                'clip_scores': clip_results['scores'],
                'top_matches': clip_results['top_matches'],
                'entropy': self._calculate_entropy(image)
            }
        }
    
    def _detect_noise(self, image: Image.Image) -> tuple:
        """
        Detect if image is pure noise
        
        Returns:
            (is_noise, noise_score)
        """
        # Convert to numpy array
        img_array = np.array(image)
        
        # Calculate entropy (randomness)
        entropy = self._calculate_entropy(image)
        
        # Calculate edge density (structured content)
        from scipy.ndimage import sobel
        gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
        edges = np.hypot(sobel(gray, axis=0), sobel(gray, axis=1))
        edge_density = np.mean(edges > 30)
        
        # High entropy + low edge density = noise
        noise_score = entropy * (1 - edge_density)
        
        is_noise = noise_score > self.anomaly_threshold
        
        return is_noise, noise_score
    
    def _calculate_entropy(self, image: Image.Image) -> float:
        """
        Calculate image entropy (measure of randomness)
        """
        # Convert to grayscale
        gray = image.convert('L')
        histogram = gray.histogram()
        
        # Normalize histogram
        histogram = np.array(histogram) / sum(histogram)
        
        # Remove zeros
        histogram = histogram[histogram > 0]
        
        # Calculate entropy
        entropy = -np.sum(histogram * np.log2(histogram))
        
        # Normalize to 0-1 range (max entropy for 8-bit = 8)
        return entropy / 8.0
    
    def _clip_analysis(self, image: Image.Image) -> Dict[str, Any]:
        """
        Perform CLIP semantic analysis
        
        Returns:
            Dictionary with CLIP scores and matches
        """
        with torch.no_grad():
            # Preprocess and encode image
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity with significance prompts
            sig_similarities = (image_features @ self.sig_features.T).squeeze(0)
            sig_scores = sig_similarities.cpu().numpy()
            
            # Calculate similarity with noise prompts
            noise_similarities = (image_features @ self.noise_features.T).squeeze(0)
            noise_scores = noise_similarities.cpu().numpy()
            
            # Get top matches
            top_indices = np.argsort(sig_scores)[-3:][::-1]
            top_matches = [
                (self.SIGNIFICANCE_PROMPTS[i], float(sig_scores[i]))
                for i in top_indices
            ]
            
            # Calculate overall semantic score
            # (max significance score minus max noise score)
            semantic_score = float(np.max(sig_scores) - np.max(noise_scores))
            semantic_score = max(0, min(1, semantic_score))  # Clamp to [0, 1]
            
            return {
                'scores': {prompt: float(score) for prompt, score in 
                          zip(self.SIGNIFICANCE_PROMPTS, sig_scores)},
                'top_matches': top_matches,
                'top_match': top_matches[0][0],
                'semantic_score': semantic_score
            }
    
    def _calculate_significance_score(self, clip_results: Dict, noise_score: float) -> float:
        """
        Calculate final significance score
        
        Combines:
        - CLIP semantic score (60%)
        - Inverse noise score (40%)
        """
        semantic_weight = 0.6
        noise_weight = 0.4
        
        semantic_score = clip_results['semantic_score']
        anti_noise_score = 1.0 - noise_score
        
        final_score = (
            semantic_score * semantic_weight +
            anti_noise_score * noise_weight
        )
        
        return float(final_score)
    
    def test_models(self) -> bool:
        """
        Test if models are working correctly
        
        Returns:
            True if tests pass
        """
        try:
            # Create test image
            test_image = Image.new('RGB', (224, 224), color='white')
            
            # Run analysis
            result = self.analyze(test_image)
            
            # Check result structure
            assert 'is_significant' in result
            assert 'score' in result
            assert 0 <= result['score'] <= 1
            
            logger.info("Model test passed")
            return True
            
        except Exception as e:
            logger.error(f"Model test failed: {e}")
            return False