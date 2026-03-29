"""
Domain-Specific AI Agents
Phase 4 Feature
"""

import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DomainAgent(ABC):
    """Base class for domain-specific agents."""
    
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain
        self.knowledge_base = []
        logger.info(f"Initialized {name} agent for {domain}")
    
    @abstractmethod
    async def handle_query(self, query: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Handle domain-specific query."""
        pass
    
    @abstractmethod
    def get_domain_keywords(self) -> List[str]:
        """Return keywords that trigger this agent."""
        pass


class AgricultureAgent(DomainAgent):
    """Agent for agricultural queries and farming advice."""
    
    KEYWORDS = [
        'खेती', 'फसल', 'बीज', 'सिंचाई', 'कीटनाशक',  # Hindi
        'விவசாயம்', 'பயிர்', 'விதை', 'பாசனம்',  # Tamil
        'మరుస†', 'పంట', 'విత్తనం', 'నీటిపారుదల',  # Telugu
    ]
    
    KNOWLEDGE = {
        'rice': 'चावल उगाने के लिए: मिट्टी का pH 5.5-7.0, तापमान 20-30°C, वार्षिक वर्षा 1200-1500mm चाहिए।',
        'wheat': 'गेहूं बोने का समय: अक्टूबर-नवंबर, तापमान 20-25°C सर्वोत्तम है।',
        'pest': 'कीट नियंत्रण: नीम का तेल, जैव कीटनाशक, और फसल चक्र प्रभावी हैं।',
    }
    
    def __init__(self):
        super().__init__("Agriculture Agent", "Agriculture & Farming")
    
    async def handle_query(self, query: str, context: Dict[str, Any]) -> Dict[str, str]:
        query_lower = query.lower()
        
        # Simple keyword matching for demonstration
        for crop, advice in self.KNOWLEDGE.items():
            if crop in query_lower:
                return {
                    "response": advice,
                    "domain": "agriculture",
                    "confidence": 0.85
                }
        
        return {
            "response": "कृषि विषय पर जानकारी के लिए कृपया अधिक विवरण दें।",
            "domain": "agriculture",
            "confidence": 0.5
        }
    
    def get_domain_keywords(self) -> List[str]:
        return self.KEYWORDS


class HealthcareAgent(DomainAgent):
    """Agent for healthcare and medical queries."""
    
    KEYWORDS = [
        'बुखार', 'खांसी', 'सर्दी', 'दर्द', 'स्वास्थ्य',  # Hindi
        'காய்ச்சல்', 'இருமல்', 'சளி', 'நோய்',  # Tamil
        'జ్వరం', 'దగ్గు', 'దశలు', 'సంబంధ',  # Telugu
    ]
    
    KNOWLEDGE = {
        'fever': 'बुखार: तरल पदार्थ लें, आराम करें, और घरेलू हल्दी दूध का उपयोग करें। अगर 103F से ऊपर है तो डॉक्टर को देखें।',
        'cough': 'खांसी: शहद, अदरक, और नींबू का मिश्रण प्रभावी है। 2 सप्ताह से अधिक खांसी के लिए चिकित्सा सहायता लें।',
        'hygiene': 'स्वच्छता: साबुन से 20 सेकंड के लिए हाथ धोएं, खांसते समय मुंह ढकें, और साफ पानी पिएं।',
    }
    
    def __init__(self):
        super().__init__("Healthcare Agent", "Healthcare & Wellness")
    
    async def handle_query(self, query: str, context: Dict[str, Any]) -> Dict[str, str]:
        query_lower = query.lower()
        
        # Keyword matching
        for condition, advice in self.KNOWLEDGE.items():
            if condition in query_lower:
                return {
                    "response": advice,
                    "domain": "healthcare",
                    "confidence": 0.80,
                    "disclaimer": "यह चिकित्सा सलाह नहीं है। गंभीर लक्षणों के लिए डॉक्टर से मिलें।"
                }
        
        return {
            "response": "स्वास्थ्य संबंधी प्रश्न के लिए अधिक जानकारी साझा करें।",
            "domain": "healthcare",
            "confidence": 0.5
        }
    
    def get_domain_keywords(self) -> List[str]:
        return self.KEYWORDS


class EducationAgent(DomainAgent):
    """Agent for education and learning queries."""
    
    KEYWORDS = [
        'पढ़ाई', 'शिक्षा', 'विज्ञान', 'गणित', 'इतिहास',  # Hindi
        'கல்வி', 'பாடம்', 'விஞ்ஞானம்', 'கணிதம்',  # Tamil
        'విద్య', 'పాఠం', 'గణితం', 'జీవశాస్త్రం',  # Telugu
    ]
    
    KNOWLEDGE = {
        'math': 'गणित: प्रतिदिन अभ्यास महत्वपूर्ण है। बुनियादी अवधारणाओं को समझें, सूत्र याद न करें।',
        'science': 'विज्ञान: प्रयोग करें और अवलोकन करें। सिद्धांतों को यथार्थ अनुप्रयोगों से जोड़ें।',
        'history': 'इतिहास: समय-सारणी याद रखें, महत्वपूर्ण तारीखें और कारण समझें।',
    }
    
    def __init__(self):
        super().__init__("Education Agent", "Education & Learning")
    
    async def handle_query(self, query: str, context: Dict[str, Any]) -> Dict[str, str]:
        query_lower = query.lower()
        
        for subject, advice in self.KNOWLEDGE.items():
            if subject in query_lower:
                return {
                    "response": advice,
                    "domain": "education",
                    "confidence": 0.85
                }
        
        return {
            "response": "शिक्षा संबंधी प्रश्न के लिए विषय निर्दिष्ट करें।",
            "domain": "education",
            "confidence": 0.5
        }
    
    def get_domain_keywords(self) -> List[str]:
        return self.KEYWORDS


class AgentOrchestrator:
    """Orchestrates multiple domain agents."""
    
    def __init__(self):
        self.agents = [
            AgricultureAgent(),
            HealthcareAgent(),
            EducationAgent(),
        ]
        logger.info(f"AgentOrchestrator initialized with {len(self.agents)} agents")
    
    async def route_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route query to appropriate agent or handle generically.
        
        Args:
            query: User query
            context: Request context
            
        Returns:
            Response from best matching agent
        """
        query_lower = query.lower()
        
        # Find best matching agent
        best_agent = None
        best_score = 0
        
        for agent in self.agents:
            keywords = agent.get_domain_keywords()
            matching_keywords = sum(1 for kw in keywords if kw.lower() in query_lower)
            
            if matching_keywords > best_score:
                best_agent = agent
                best_score = matching_keywords
        
        if best_agent and best_score > 0:
            logger.info(f"Routing to {best_agent.name}")
            result = await best_agent.handle_query(query, context)
            return {
                **result,
                "agent": best_agent.name,
                "domain": best_agent.domain
            }
        
        # Generic response if no domain match
        return {
            "response": "सामान्य प्रश्न: कृपया अधिक जानकारी प्रदान करें।",
            "domain": "general",
            "confidence": 0.5,
            "agent": "General"
        }
    
    def get_agents_info(self) -> List[Dict[str, Any]]:
        """Get information about all agents."""
        return [
            {
                "name": agent.name,
                "domain": agent.domain,
                "keywords": agent.get_domain_keywords()[:5]  # First 5 keywords
            }
            for agent in self.agents
        ]
