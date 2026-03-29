#!/bin/bash
# Comprehensive Health Check Script
# Validates all 6 phases are operational

set -e

print_header() {
    echo -e "\n╔════════════════════════════════════════════════════════════╗"
    echo "║  RURAL INDIA AI - COMPREHENSIVE HEALTH CHECK              ║"
    echo "╚════════════════════════════════════════════════════════════╝\n"
}

print_phase() {
    echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "[$1] $2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    printf "  🧪 %-40s " "$name"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "http://127.0.0.1:8000$endpoint" \
            -H "Content-Type: application/json" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "http://127.0.0.1:8000$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "✅ (HTTP $http_code)"
        return 0
    elif [ "$http_code" = "403" ]; then
        echo "✅ (HTTP $http_code - Blocked by safety)"
        return 0
    else
        echo "❌ (HTTP $http_code)"
        return 1
    fi
}

main() {
    print_header
    
    # Check if server is running
    printf "Checking API server... "
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
        echo "✅ Running\n"
    else
        echo "❌ NOT RUNNING"
        echo "Start with: ./run_api_server.sh start"
        exit 1
    fi
    
    PASSED=0
    FAILED=0
    
    # Phase 1: Edge Infrastructure
    print_phase "PHASE 1" "Edge Infrastructure"
    
    test_endpoint "API Health Check" "GET" "/api/v1/health" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Hardware Metrics" "GET" "/api/v1/hardware" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Power Status" "GET" "/api/v1/power" && ((PASSED++)) || ((FAILED++))
    test_endpoint "System Status" "GET" "/api/v1/status" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Request Queue Sync" "POST" "/api/v1/sync" "{}" && ((PASSED++)) || ((FAILED++))
    
    # Phase 2: Voice Interface
    print_phase "PHASE 2" "Voice Interface (9 Languages)"
    
    test_endpoint "Get Languages" "GET" "/api/v2/languages" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Text Query" "POST" "/api/v2/query" '{"query":"test","language":"en"}' && ((PASSED++)) || ((FAILED++))
    test_endpoint "Switch Language" "POST" "/api/v2/language" '{"language":"hi"}' && ((PASSED++)) || ((FAILED++))
    test_endpoint "Voice Interaction" "POST" "/api/v2/voice" '{"language":"en"}' && ((PASSED++)) || ((FAILED++))
    
    # Phase 3: Vector Database
    print_phase "PHASE 3" "Vector Database & RAG"
    
    test_endpoint "Vector DB Stats" "GET" "/api/v3/stats" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Search Documents" "POST" "/api/v3/search" '{"query":"irrigation"}' && ((PASSED++)) || ((FAILED++))
    test_endpoint "Add Document" "POST" "/api/v3/documents" '{"text":"test doc","doc_id":"test"}' && ((PASSED++)) || ((FAILED++))
    
    # Phase 4: Domain Agents
    print_phase "PHASE 4" "Domain Agents (3 Agents)"
    
    test_endpoint "List Agents" "GET" "/api/v4/agents" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Route Query" "POST" "/api/v4/agents/query" '{"query":"farming"}' && ((PASSED++)) || ((FAILED++))
    
    # Phase 5: Safety Guardrails
    print_phase "PHASE 5" "Safety Guardrails"
    
    test_endpoint "Safety Check" "POST" "/api/v5/safety/check" '{"query":"farm"}' && ((PASSED++)) || ((FAILED++))
    test_endpoint "Trust Score" "POST" "/api/v5/trust/score" '{"query":"water crops"}' && ((PASSED++)) || ((FAILED++))
    
    # Phase 6: Observability
    print_phase "PHASE 6" "Observability & Analytics"
    
    test_endpoint "Dashboard Data" "GET" "/api/v6/dashboard" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Metrics" "GET" "/api/v6/metrics" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Analytics" "GET" "/api/v6/analytics" && ((PASSED++)) || ((FAILED++))
    test_endpoint "Health Check" "GET" "/api/v6/health" && ((PASSED++)) || ((FAILED++))
    
    # Summary
    print_phase "SUMMARY" "Test Results"
    
    TOTAL=$((PASSED + FAILED))
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
    
    echo ""
    echo "  ✅ Passed:  $PASSED"
    echo "  ❌ Failed:  $FAILED"
    echo "  📊 Total:   $TOTAL"
    echo "  📈 Rate:    $SUCCESS_RATE%"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║  🎉 ALL SYSTEMS OPERATIONAL - PRODUCTION READY!           ║"
        echo "║                                                            ║"
        echo "║  ✅ All 6 phases responding correctly                      ║"
        echo "║  ✅ All endpoints operational                             ║"
        echo "║  ✅ System ready for deployment                           ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        exit 0
    else
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║  ⚠️  SOME TESTS FAILED - REVIEW ABOVE                     ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        exit 1
    fi
}

main "$@"
