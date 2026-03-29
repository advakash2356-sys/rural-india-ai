#!/usr/bin/env python3
"""
CLI Tool for Rural India AI
Access the edge node from command line
"""

import asyncio
import json
import argparse
import requests
from typing import Optional, Dict, Any
import sys

class RuralAsiaAICLI:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check system health"""
        try:
            resp = self.session.get(f"{self.api_url}/api/v1/health")
            resp.raise_for_status()
            data = resp.json()
            self._print_status("✓ System Health", data)
        except Exception as e:
            self._print_error(f"Health check failed: {e}")
    
    def status(self):
        """Get system status"""
        try:
            resp = self.session.get(f"{self.api_url}/api/v1/status")
            resp.raise_for_status()
            data = resp.json()
            self._print_status("System Status", data)
        except Exception as e:
            self._print_error(f"Status fetch failed: {e}")
    
    def hardware(self):
        """Get hardware metrics"""
        try:
            resp = self.session.get(f"{self.api_url}/api/v1/hardware")
            resp.raise_for_status()
            data = resp.json()
            print("\n📊 Hardware Metrics")
            print("=" * 40)
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"{key}: {value}")
        except Exception as e:
            self._print_error(f"Hardware fetch failed: {e}")
    
    def query(self, text: str, language: str = "hi", use_rag: bool = True):
        """Process query"""
        try:
            resp = self.session.post(
                f"{self.api_url}/api/v2/query",
                json={
                    "query": text,
                    "language": language,
                    "use_rag": use_rag
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            print("\n💬 Query Response")
            print("=" * 40)
            print(f"Query: {text}")
            print(f"Language: {language}")
            print(f"Latency: {data.get('latency_ms', 0):.2f}ms")
            print(f"Safety: {data.get('safety', 'unknown')}")
            print(f"Trust Score: {data.get('trust_score', 0):.2f}")
            print(f"\nResponse: {json.dumps(data.get('response'), indent=2)}")
        except Exception as e:
            self._print_error(f"Query failed: {e}")
    
    def agents(self):
        """List domain agents"""
        try:
            resp = self.session.get(f"{self.api_url}/api/v4/agents")
            resp.raise_for_status()
            data = resp.json()
            
            print("\n🤖 Domain Agents")
            print("=" * 40)
            print(f"Total Agents: {data['count']}")
            for agent in data['agents']:
                print(f"\n{agent['name']}:")
                print(f"  Type: {agent.get('domain', 'unknown')}")
                print(f"  Keywords: {agent.get('keywords', [])}")
        except Exception as e:
            self._print_error(f"Agents fetch failed: {e}")
    
    def search(self, query: str):
        """Search vector database"""
        try:
            resp = self.session.post(
                f"{self.api_url}/api/v3/search",
                json={"query": query}
            )
            resp.raise_for_status()
            data = resp.json()
            
            print(f"\n🔍 Search Results for: {query}")
            print("=" * 40)
            for i, result in enumerate(data['results'], 1):
                print(f"\n{i}. Similarity: {result['similarity']:.3f}")
                print(f"   ID: {result['doc_id']}")
                print(f"   Text: {result['text']}")
        except Exception as e:
            self._print_error(f"Search failed: {e}")
    
    def dashboard(self):
        """Get dashboard"""
        try:
            resp = self.session.get(f"{self.api_url}/api/v6/dashboard")
            resp.raise_for_status()
            data = resp.json()
            self._print_status("📈 Dashboard", data)
        except Exception as e:
            self._print_error(f"Dashboard fetch failed: {e}")
    
    def analytics(self):
        """Get analytics"""
        try:
            resp = self.session.get(f"{self.api_url}/api/v6/analytics")
            resp.raise_for_status()
            data = resp.json()
            
            print("\n📊 Usage Analytics")
            print("=" * 40)
            print(f"Total Interactions: {data.get('total_interactions', 0)}")
            print(f"Avg Latency: {data.get('avg_latency_ms', 0):.2f}ms")
            if 'languages' in data:
                print(f"\nLanguages:")
                for lang, count in data['languages'].items():
                    print(f"  {lang}: {count}")
        except Exception as e:
            self._print_error(f"Analytics fetch failed: {e}")
    
    def safety_check(self, text: str):
        """Check text safety"""
        try:
            resp = self.session.post(
                f"{self.api_url}/api/v5/safety/check",
                json={"query": text}
            )
            resp.raise_for_status()
            data = resp.json()
            
            print("\n🛡️ Safety Check")
            print("=" * 40)
            print(f"Text: {text}")
            print(f"Safety Level: {data['safety_level']}")
            print(f"Issues: {', '.join(data['issues']) if data['issues'] else 'None'}")
            if data.get('bias_analysis'):
                print(f"Bias: {data['bias_analysis']}")
        except Exception as e:
            self._print_error(f"Safety check failed: {e}")
    
    def _print_status(self, title: str, data: Dict[str, Any]):
        """Pretty print status"""
        print(f"\n{title}")
        print("=" * 40)
        print(json.dumps(data, indent=2))
    
    def _print_error(self, msg: str):
        """Print error"""
        print(f"\n❌ {msg}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Rural India AI CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./cli.py health                           # Check system health
  ./cli.py status                           # Get system status
  ./cli.py query "मेरे खेत में कीड़े हैं"   # Ask question in Hindi
  ./cli.py query "ಕುಡುಕೆ" --language=kn   # Ask in Kannada
  ./cli.py agents                           # List agents
  ./cli.py search "irrigation"              # Search documents
  ./cli.py dashboard                        # Get dashboard
  ./cli.py safety-check "some text"         # Check safety
        """
    )
    
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Health command
    subparsers.add_parser("health", help="Check system health")
    
    # Status command
    subparsers.add_parser("status", help="Get system status")
    
    # Hardware command
    subparsers.add_parser("hardware", help="Get hardware metrics")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Process query")
    query_parser.add_argument("text", help="Query text")
    query_parser.add_argument("--language", "-l", default="hi", help="Query language (default: hi)")
    query_parser.add_argument("--no-rag", action="store_true", help="Disable RAG")
    
    # Agents command
    subparsers.add_parser("agents", help="List domain agents")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    
    # Dashboard command
    subparsers.add_parser("dashboard", help="Get dashboard")
    
    # Analytics command
    subparsers.add_parser("analytics", help="Get usage analytics")
    
    # Safety command
    safety_parser = subparsers.add_parser("safety-check", help="Check safety")
    safety_parser.add_argument("text", help="Text to check")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = RuralAsiaAICLI(args.api_url)
    
    if args.command == "health":
        cli.health_check()
    elif args.command == "status":
        cli.status()
    elif args.command == "hardware":
        cli.hardware()
    elif args.command == "query":
        cli.query(args.text, args.language, not args.no_rag)
    elif args.command == "agents":
        cli.agents()
    elif args.command == "search":
        cli.search(args.query)
    elif args.command == "dashboard":
        cli.dashboard()
    elif args.command == "analytics":
        cli.analytics()
    elif args.command == "safety-check":
        cli.safety_check(args.text)


if __name__ == "__main__":
    main()
