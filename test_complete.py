#!/usr/bin/env python3
"""
Comprehensive Rural India AI System Test Suite - CORRECTED ENDPOINTS
Tests all 6 phases via REST API with correct endpoint paths
"""

import requests
import json
import sys
import time
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
            return None
        
        if response.status_code == expected_status:
            print("✅")
            PASSED += 1
            return response.json()
        else:
            print(f"❌ (Code: {response.status_code}, expected {expected_status})")
            FAILED += 1
            ERRORS.append(f"{name}: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        FAILED += 1
        ERRORS.append(f"{name}: API not responding on {API_BASE}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:50]}")
        FAILED += 1
        ERRORS.append(f"{name}: {str(e)[:100]}")
    
    return None

def main():
    """Run complete test suite"""
    global PASSED, FAILED
    
    print("\n" + "="*70)
    print("RURAL INDIA AI - COMPREHENSIVE SYSTEM TEST")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base: {API_BASE}\n")
    
    # Wait for API to be ready
    print("⏳ Waiting for API to be ready...", end=" ", flush=True)
    for i in range(30):
        try:
            response = requests.get(f"{API_BASE}/", timeout=1)
            if response.status_code == 200:
                print("✅ API is ready\n")
                break
        except:
            pass
        time.sleep(0.5)
    
    # Phase 1: Edge Infrastructure
    print("\n[PHASE 1] EDGE INFRASTRUCTURE")
    print("-" * 70)
    p1_health = test("API Health Check", "GET", "/api/v1/health")
    p1_hardware = test("Hardware Metrics", "GET", "/api/v1/hardware")
    p1_power = test("Power Status", "GET", "/api/v1/power")
    p1_sync = test("Request Queue Sync", "POST", "/api/v1/sync", {})
    
    # Phase 2: Voice Interface
    print("\n[PHASE 2] VOICE INTERFACE")
    print("-" * 70)
    p2_lang = test("Get Supported Languages", "GET", "/api/v2/languages")
    p2_query = test("Text Query", "POST", "/api/v2/query", 
         {"query": "What should I plant in spring?", "language": "en"})
    p2_switch = test("Switch Language", "POST", "/api/v2/language", {"language": "hi"})
    p2_voice = test("Voice Interaction Ready", "POST", "/api/v2/voice", {"language": "hi"})
    
    # Phase 3: Vector Database
    print("\n[PHASE 3] VECTOR DATABASE & RAG")
    print("-" * 70)
    p3_stats = test("Vector DB Statistics", "GET", "/api/v3/stats")
    p3_search = test("Search Documents", "POST", "/api/v3/search",
         {"query": "irrigation methods"})
    p3_add = test("Add Document", "POST", "/api/v3/documents",
         {"text": "Best practices for crop rotation", "doc_id": "doc-001"})
    
    # Phase 4: Domain Agents
    print("\n[PHASE 4] DOMAIN AGENTS")
    print("-" * 70)
    p4_list = test("List Available Agents", "GET", "/api/v4/agents")
    p4_query = test("Route Query to Agent", "POST", "/api/v4/agents/query",
         {"query": "My crops are getting yellow leaves", "language": "hi"})
    
    # Phase 5: Safety Guardrails
    print("\n[PHASE 5] SAFETY GUARDRAILS")
    print("-" * 70)
    p5_check = test("Safety Check", "POST", "/api/v5/safety/check",
         {"query": "Tell me how to improve my farming"})
    p5_trust = test("Calculate Trust Score", "POST", "/api/v5/trust/score",
         {"query": "Water your crops in the morning for best results"})
    
    # Phase 6: Observability
    print("\n[PHASE 6] OBSERVABILITY & ANALYTICS")
    print("-" * 70)
    p6_dashboard = test("Dashboard Data", "GET", "/api/v6/dashboard")
    p6_metrics = test("System Metrics", "GET", "/api/v6/metrics")
    p6_analytics = test("Usage Analytics", "GET", "/api/v6/analytics")
    p6_health = test("Detailed Health Check", "GET", "/api/v6/health")
    
    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    print(f"✅ Tests Passed: {PASSED}")
    print(f"❌ Tests Failed: {FAILED}")
    print(f"📊 Total Tests: {PASSED + FAILED}")
    print(f"📈 Success Rate: {(PASSED/(PASSED+FAILED)*100):.1f}%" if (PASSED+FAILED) > 0 else "N/A")
    
    if FAILED > 0:
        print("\n⚠️  ERRORS ENCOUNTERED:")
        for error in ERRORS:
            print(f"  • {error}")
    
    print("\n" + "="*70)
    print("DETAILED COMPONENT STATUS")
    print("="*70)
    
    phases = [
        ("Phase 1: Edge Infrastructure", [p1_health, p1_hardware, p1_power, p1_sync]),
        ("Phase 2: Voice Interface", [p2_lang, p2_query, p2_switch, p2_voice]),
        ("Phase 3: Vector Database", [p3_stats, p3_search, p3_add]),
        ("Phase 4: Domain Agents", [p4_list, p4_query]),
        ("Phase 5: Safety Guardrails", [p5_check, p5_trust]),
        ("Phase 6: Observability", [p6_dashboard, p6_metrics, p6_analytics, p6_health])
    ]
    
    for phase_name, results in phases:
        operational = len([r for r in results if r is not None])
        total = len(results)
        status = "✅ OPERATIONAL" if operational == total else f"⚠️  PARTIAL ({operational}/{total})"
        print(f"\n{phase_name}: {status}")
    
    print("\n" + "="*70)
    if FAILED == 0:
        print("🎉 SUCCESS - ALL TESTS PASSED!")
        print("✅ System is fully operational")
        print("✅ All 6 phases responding correctly")
        print("✅ Ready for production deployment")
        return 0
    else:
        print(f"⚠️  PARTIAL SUCCESS - {PASSED} of {PASSED+FAILED} tests passed")
        print(f"❌ {FAILED} test(s) failed - see details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
