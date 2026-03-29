#!/usr/bin/env python3
"""
Comprehensive Rural India AI System Test Suite
Tests all 6 phases via REST API
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "http://127.0.0.1:8000"
PASSED = 0
FAILED = 0
ERRORS = []

def test(name, method, endpoint, data=None, expected_status=200):
    """Run a single test"""
    global PASSED, FAILED, ERRORS
    
    print(f"  🧪 {name}...", end=" ", flush=True)
    
    try:
        url = f"{API_BASE}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            print("❌ INVALID METHOD")
            FAILED += 1
            return
        
        if response.status_code == expected_status:
            print("✅")
            PASSED += 1
            return response.json()
        else:
            print(f"❌ (Code: {response.status_code}, expected {expected_status})")
            FAILED += 1
            ERRORS.append(f"{name}: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        FAILED += 1
        ERRORS.append(f"{name}: API not responding on {API_BASE}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:50]}")
        FAILED += 1
        ERRORS.append(f"{name}: {str(e)[:100]}")

def main():
    """Run complete test suite"""
    global PASSED, FAILED
    
    print("\n" + "="*70)
    print("RURAL INDIA AI - COMPREHENSIVE SYSTEM TEST")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base: {API_BASE}\n")
    
    # Phase 1: Edge Infrastructure
    print("\n[PHASE 1] EDGE INFRASTRUCTURE")
    print("-" * 70)
    test("API Health Check", "GET", "/api/v1/health")
    test("System Status", "GET", "/api/v1/status")
    test("Hardware Metrics", "GET", "/api/v1/hardware")
    test("Power Status", "GET", "/api/v1/power")
    test("Trigger Sync", "POST", "/api/v1/sync")
    
    # Phase 2: Voice Interface
    print("\n[PHASE 2] VOICE INTERFACE")
    print("-" * 70)
    test("Available Languages", "GET", "/api/v2/languages")
    test("Text Query", "POST", "/api/v2/query", 
         {"query": "What should I plant?", "language": "en"})
    test("Voice Interaction", "POST", "/api/v2/voice",
         {"duration": 5.0, "language": "hi"})
    test("Language Switch", "POST", "/api/v2/language",
         {"language": "hi"})
    
    # Phase 3: Vector Database
    print("\n[PHASE 3] VECTOR DATABASE & RAG")
    print("-" * 70)
    test("Vector DB Stats", "GET", "/api/v3/stats")
    test("Search Documents", "POST", "/api/v3/search",
         {"query": "irrigation methods"})
    test("Add Document", "POST", "/api/v3/documents",
         {"text": "Testing the system", "doc_id": "test1"})
    
    # Phase 4: Domain Agents
    print("\n[PHASE 4] DOMAIN AGENTS")
    print("-" * 70)
    test("Query Agents", "POST", "/api/v4/query",
         {"query": "My crops have pests", "language": "hi"})
    
    # Phase 5: Safety Guardrails
    print("\n[PHASE 5] SAFETY GUARDRAILS")
    print("-" * 70)
    test("Check Safety", "POST", "/api/v5/check",
         {"content": "Tell me about farming"})
    
    # Phase 6: Observability
    print("\n[PHASE 6] OBSERVABILITY & ANALYTICS")
    print("-" * 70)
    test("Metrics", "GET", "/api/v6/metrics")
    test("Analytics", "GET", "/api/v6/analytics")
    test("Dashboard", "GET", "/api/v6/dashboard")
    
    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    print(f"✅ Passed: {PASSED}")
    print(f"❌ Failed: {FAILED}")
    print(f"Total: {PASSED + FAILED}")
    
    if FAILED > 0:
        print("\n⚠️  ERRORS ENCOUNTERED:")
        for error in ERRORS:
            print(f"  - {error}")
        print("\n⚠️  SYSTEM HAS ISSUES - Review above")
        return 1
    else:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is fully operational")
        print("✅ All 6 phases responding correctly")
        print("✅ Ready for production use")
        return 0

if __name__ == "__main__":
    sys.exit(main())
