#!/bin/bash

# Admin Stats API 테스트 스크립트

echo "=== Admin Stats API Test ==="

# 1. 새 관리자 계정 생성
echo -e "\n[1] Creating admin account..."
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin_final@example.com","password":"Admin1234!","username":"admin_final"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
    echo "Failed to create admin account. Using existing admin_test@example.com..."
    # 기존 계정으로 로그인 (signup에서 받은 토큰 사용)
    ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/signup" \
      -H "Content-Type: application/json" \
      -d '{"email":"unique_admin_'"$RANDOM"'@example.com","password":"Admin1234!","username":"admin'"$RANDOM"'"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
fi

echo "Admin token: ${ADMIN_TOKEN:0:50}..."

# 2. DB에서 관리자로 승격
echo -e "\n[2] Upgrading to superuser..."
/opt/homebrew/opt/postgresql@14/bin/psql -d tarot_db -c "UPDATE users SET is_superuser = true WHERE id IN (SELECT id FROM users ORDER BY created_at DESC LIMIT 1);" 2>/dev/null

# 3. Admin Stats API 호출
echo -e "\n[3] Testing GET /api/v1/admin/stats..."
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/stats" | python3 -m json.tool

# 4. Period Stats API 호출
echo -e "\n[4] Testing GET /api/v1/admin/stats/period?days=7..."
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/stats/period?days=7" | python3 -m json.tool

# 5. Spread Type Stats API 호출
echo -e "\n[5] Testing GET /api/v1/admin/stats/spread-types..."
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/stats/spread-types" | python3 -m json.tool

echo -e "\n=== Test Complete ==="
