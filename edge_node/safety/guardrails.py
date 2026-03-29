"""
Trust & Safety Guardrails
Phase 5 Feature
"""

import json
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety levels for responses."""
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


class GuardrailsEngine:
    """
    Safety and trust guardrails for AI responses.
    Prevents harmful, biased, or inappropriate outputs.
    """
    
    # Harmful keywords and patterns
    HARMFUL_PATTERNS = {
        'violence': [r'मारना|चोट|हिंसा|हत्या|सूली|तोड़ना|नष्ट'],  # Hindi
        'hate': [r'नफरत|भेदभाव|दलित|अल्पसंख्यक'],
        'explicit': [r'सेक्स|यौन|अश्लील'],
    }
    
    # Biased language patterns
    BIAS_PATTERNS = {
        'gender': [r'महिलाएं.*कमजोर|पुरुष.*मजबूत|लड़का.*लड़की'],
        'caste': [r'उच्च.*जाति|निम्न.*जाति'],
        'religion': [r'धर्म.*बेहतर'],
    }
    
    def __init__(self):
        self.blocked_count = 0
        self.warned_count = 0
        logger.info("GuardrailsEngine initialized")
    
    def check_input(self, text: str) -> Tuple[SafetyLevel, List[str]]:
        """
        Check if input is safe to process.
        
        Args:
            text: Input text to check
            
        Returns:
            (SafetyLevel, list of issues found)
        """
        issues = []
        
        # Check for harmful content
        for category, patterns in self.HARMFUL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append(f"harmful_{category}")
        
        # Check for biased language
        for category, patterns in self.BIAS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append(f"bias_{category}")
        
        # Check word count (prevent spam)
        if len(text.split()) > 1000:
            issues.append("excessive_length")
        
        # Determine safety level
        if len(issues) > 2:
            self.blocked_count += 1
            return SafetyLevel.BLOCKED, issues
        elif len(issues) > 0:
            self.warned_count += 1
            return SafetyLevel.WARNING, issues
        
        return SafetyLevel.SAFE, []
    
    def check_output(self, text: str) -> Tuple[SafetyLevel, List[str]]:
        """
        Check if output is safe to present to user.
        
        Args:
            text: Output text to check
            
        Returns:
            (SafetyLevel, list of issues found)
        """
        issues = []
        
        # Check for harmful content in output
        for category, patterns in self.HARMFUL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append(f"output_harmful_{category}")
        
        # Check for personally identifiable information
        if self._contains_pii(text):
            issues.append("personal_information")
        
        # Check for medical misinformation
        if self._is_dangerous_medical_advice(text):
            issues.append("dangerous_medical_advice")
        
        if len(issues) > 0:
            self.blocked_count += 1
            return SafetyLevel.BLOCKED, issues
        
        return SafetyLevel.SAFE, []
    
    def filter_output(self, text: str, aggressive: bool = False) -> str:
        """
        Filter output to remove sensitive content.
        
        Args:
            text: Text to filter
            aggressive: Apply aggressive filtering
            
        Returns:
            Filtered text
        """
        filtered = text
        
        # Mask harmful phrases
        for category, patterns in self.HARMFUL_PATTERNS.items():
            for pattern in patterns:
                filtered = re.sub(pattern, "[removed]", filtered, flags=re.IGNORECASE)
        
        if aggressive:
            # Additional filtering
            for category, patterns in self.BIAS_PATTERNS.items():
                for pattern in patterns:
                    filtered = re.sub(pattern, "[filtered]", filtered, flags=re.IGNORECASE)
        
        return filtered
    
    @staticmethod
    def _contains_pii(text: str) -> bool:
        """Check if text contains personally identifiable information."""
        pii_patterns = [
            r'\d{10}',  # Phone number
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\d{10,}',  # ID number
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    @staticmethod
    def _is_dangerous_medical_advice(text: str) -> bool:
        """Check if text contains potentially dangerous medical advice."""
        dangerous_phrases = [
            r'stop.*medicine',
            r'बिना.*डॉक्टर',  # Hindi: without doctor
            r'तुरंत.*ठीक',  # Hindi: instantly cure
            r'आत्महत्या',  # Hindi: suicide
        ]
        
        for phrase in dangerous_phrases:
            if re.search(phrase, text, re.IGNORECASE):
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get guardrail statistics."""
        return {
            "blocked_inputs": self.blocked_count,
            "warned_inputs": self.warned_count,
            "total_filtered": self.blocked_count + self.warned_count
        }


class BiasDetector:
    """
    Detects and reports bias in AI responses.
    Helps ensure fair and equitable outputs across demographics.
    """
    
    BIAS_CATEGORIES = {
        'gender': {
            'male_terms': ['पुरुष', 'भाई', 'बेटा', 'पिता'],
            'female_terms': ['महिला', 'बहन', 'बेटी', 'माता'],
        },
        'caste': {
            'upper': ['ब्राह्मण', 'क्षत्रिय'],
            'lower': ['दलित', 'अछूत'],
        },
    }
    
    def __init__(self):
        logger.info("BiasDetector initialized")
    
    def analyze_balance(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for potential bias.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with bias analysis
        """
        results = {
            "likely_bias": False,
            "categories": {},
            "concerns": []
        }
        
        text_lower = text.lower()
        
        for category, terms_dict in self.BIAS_CATEGORIES.items():
            category_results = {"distribution": {}}
            
            for group, terms in terms_dict.items():
                count = sum(
                    len(re.findall(r'\b' + re.escape(term) + r'\b', text_lower))
                    for term in terms
                )
                category_results["distribution"][group] = count
            
            results["categories"][category] = category_results
            
            # Check for imbalance
            dist = category_results["distribution"]
            if dist and max(dist.values()) > 0:
                total = sum(dist.values())
                max_ratio = max(dist.values()) / total
                
                if max_ratio > 0.7:  # One group dominates
                    results["likely_bias"] = True
                    results["concerns"].append(
                        f"Potential {category} bias detected"
                    )
        
        return results
    
    def suggest_improvements(self, text: str) -> List[str]:
        """Suggest improvements to reduce bias."""
        suggestions = []
        
        analysis = self.analyze_balance(text)
        
        if analysis["likely_bias"]:
            suggestions.append("Ensure representation of all genders")
            suggestions.append("Include diverse cultural references")
            suggestions.append("Use inclusive language")
        
        if "महिला" not in text.lower() and "पुरुष" in text.lower():
            suggestions.append("Consider mentioning both genders")
        
        return suggestions


class TrustScore:
    """
    Calculates trust scores for AI responses.
    Higher scores indicate more reliable, verifiable information.
    """
    
    def __init__(self):
        self.source_credibility = 0.7  # Default credibility
        logger.info("TrustScore initialized")
    
    def compute_score(self, 
                     text: str,
                     source: Optional[str] = None,
                     has_evidence: bool = False) -> float:
        """
        Compute trust score for a response.
        
        Args:
            text: Response text
            source: Source of information
            has_evidence: Whether response has supporting evidence
            
        Returns:
            Trust score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Add points for characteristics
        if has_evidence:
            score += 0.2
        
        if source and source in ['official', 'research', 'verified']:
            score += 0.15
        
        # Check uncertainty language
        uncertainty_words = ['शायद', 'संभवतः', 'अनुमान', 'हो सकता']
        uncertainty_count = sum(
            1 for word in uncertainty_words 
            if word.lower() in text.lower()
        )
        
        if uncertainty_count > 0:
            score -= (0.05 * uncertainty_count)
        
        # Check empowerment language
        empowerment_words = ['निश्चित', 'सिद्ध', 'विश्वसनीय', 'गारंटी']
        empowerment_count = sum(
            1 for word in empowerment_words 
            if word.lower() in text.lower()
        )
        
        if empowerment_count > 0:
            score += (0.05 * min(empowerment_count, 3))
        
        # Normalize score to 0-1 range
        return max(0.0, min(1.0, score))


# Type hint
from typing import Optional
