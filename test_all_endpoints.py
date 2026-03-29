#!/usr/bin/env python3
"""Comprehensive API endpoint testing - 100% coverage"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://127.0.0.1:8000'
TIMEOUT = 5

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_endpoint(method, endpoint, data=None):
    """Test a single endpoint"""
    try:
        url = f'{BASE_URL}{endpoint}'
        if method == 'GET':
            r = requests.get(url, timeout=TIMEOUT)
        else:
            r = requests.post(url, json=data, timeout=TIMEOUT)
        
        status = '✅' if r.status_code < 400 else '❌'
        print(f'{status} {method:6} {endpoint:40} -> HTTP {r.status_code}')
        
        return r.status_code < 400
    except requests.exceptions.Timeout:
        print(f'❌ {method:6} {endpoint:40} -> TIMEOUT')
        return False
    except Exception as e:
        print(f'❌ {method:6} {endpoint:40} -> {str(e)[:25]}')
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"RURAL INDIA AI - COMPREHENSIVE ENDPOINT TEST")
    print(f"{'='*70}{Colors.END}\n")
    
    # Define all endpoints to test
    tests = [
        ("PHASE 1: Edge Infrastructure", [
            ('GET', '/api/v1/health', None),
            ('GET', '/api/v1/hardware', None),
            ('GET', '/api/v1/power', None),
            ('GET', '/api/v1/status', None),
            ('POST', '/api/v1/queue/sync', None),
        ]),
        ("PHASE 2: Voice Interface", [
            ('GET', '/api/v2/languages', None),
            ('POST', '/api/v2/query', {'query': 'Hello', 'language': 'en'}),
            ('POST', '/api/v2/voice', {'language': 'en'}),
        ]),
        ("PHASE 3: Vector Database & RAG", [
            ('GET', '/api/v3/stats', None),
            ('POST', '/api/v3/search', {'query': 'agriculture'}),
            ('POST', '/api/v3/documents', {'text': 'Test doc', 'title': 'Test'}),
        ]),
        ("PHASE 4: Domain Agents", [
            ('GET', '/api/v4/agents', None),
            ('POST', '/api/v4/agents/query', {'query': 'Crop help', 'language': 'en'}),
        ]),
        ("PHASE 5: Safety & Trust", [
            ('POST', '/api/v5/safety/check', {'text': 'Safe text'}),
            ('POST', '/api/v5/trust/score', {'text': 'Trusted text'}),
        ]),
        ("PHASE 6: Observability & Analytics", [
            ('GET', '/api/v6/dashboard', None),
            ('GET', '/api/v6/metrics', None),
            ('GET', '/api/v6/analytics', None),
            ('GET', '/api/v6/health', None),
        ]),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for phase_name, endpoints in tests:
        print(f"{Colors.BLUE}{phase_name}{Colors.END}")
        print("-" * 70)
        
        for method, endpoint, data in endpoints:
            passed = test_endpoint(method, endpoint, data)
            if passed:
                total_passed += 1
            else:
                total_failed += 1
        
        print()
    
    # Summary
    total = total_passed + total_failed
    percentage = (total_passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BLUE}{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}{Colors.END}")
    print(f"✅ Passed:  {Colors.GREEN}{total_passed}{Colors.END}")
    print(f"❌ Failed:  {Colors.RED}{total_failed}{Colors.END}")
    print(f"📊 Total:   {total}")
    print(f"📈 Success: {percentage:.1f}%")
    
    if total_failed == 0:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED - SYSTEM 100% OPERATIONAL{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  SOME TESTS FAILED - REVIEW FAILURES ABOVE{Colors.END}\n")
        return 1

if __name__ == '__main__':
    exit(main())
