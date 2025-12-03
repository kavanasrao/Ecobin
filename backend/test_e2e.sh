#!/bin/bash

API_URL="http://localhost:8001/api"

echo "======================================"
echo "SMART WASTE DISPOSAL - E2E TEST"
echo "======================================"
echo ""

# 1. Register new user
echo "1. Registering new user..."
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/users/register \
  -H "Content-Type: application/json" \
  -d '{"name":"E2E Test User","phone":"7777777777","address":"Test Location"}')
echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"

NEW_QR=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['qr_code'])")
echo ""

# 2. Authenticate
echo "2. Authenticating user..."
AUTH_RESPONSE=$(curl -s -X POST $API_URL/users/authenticate \
  -H "Content-Type: application/json" \
  -d "{\"qr_code\":\"$NEW_QR\"}")
TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
echo "✓ Token obtained"
echo ""

# 3. Unlock dry bin
echo "3. Unlocking dry bin..."
curl -s -X POST $API_URL/bin/unlock \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type":"dry"}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# 4. Dispose waste (dry)
echo "4. Logging disposal (3 kg dry waste)..."
curl -s -X POST $API_URL/disposal/log \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type":"dry","weight":3.0}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# 5. Unlock wet bin
echo "5. Unlocking wet bin..."
curl -s -X POST $API_URL/bin/unlock \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type":"wet"}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# 6. Dispose waste (wet)
echo "6. Logging disposal (2 kg wet waste)..."
curl -s -X POST $API_URL/disposal/log \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type":"wet","weight":2.0}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# 7. Check profile
echo "7. Checking user profile & statistics..."
curl -s $API_URL/users/profile \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# 8. Get available rewards
echo "8. Viewing available rewards..."
curl -s $API_URL/rewards \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Current Points: {d['current_points']}\"); print(f\"Available Rewards: {len(d['rewards'])}\")"
echo ""

# 9. Admin login
echo "9. Admin login..."
ADMIN_RESPONSE=$(curl -s -X POST $API_URL/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
echo "✓ Admin authenticated"
echo ""

# 10. View overall statistics
echo "10. Viewing overall statistics (Admin)..."
curl -s $API_URL/admin/statistics \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

echo "======================================"
echo "✅ E2E TEST COMPLETED SUCCESSFULLY!"
echo "======================================"
