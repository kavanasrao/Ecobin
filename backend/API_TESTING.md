# Smart Waste Disposal API - Testing Guide

## Quick Start Testing

### Prerequisites
- Server running on `http://localhost:8001`
- MySQL database initialized with sample data

### Sample Test Data

#### Default Admin Credentials
```
Username: admin
Password: admin123
```

#### Sample User QR Codes (from sample_data.py)
```
User 1: Rahul Sharma  | QR: c7485f5d-a1ba-4357-a1cb-c9b098180ba7
User 2: Priya Patel   | QR: 4f2d0905-3beb-4e4b-8be7-7b3a50ea3e11
User 3: Amit Kumar    | QR: 80b26ec3-ed2d-4eeb-bf3f-7fe863e31cba
User 4: Sneha Reddy   | QR: 1068ef85-ad0b-4f0f-8458-8365191d634c
User 5: Vikram Singh  | QR: f32e2c0e-0ba9-46b7-9f22-46bea785ba17
```

---

## USER FLOW TESTS

### 1. Health Check
```bash
curl http://localhost:8001/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "Smart Waste Disposal API is running"
}
```

---

### 2. User Registration
```bash
curl -X POST http://localhost:8001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "9898989898",
    "address": "123 Sample Street, City"
  }'
```

**Expected Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 7,
    "name": "John Doe",
    "phone": "9898989898",
    "qr_code": "generated-uuid-here",
    "qr_code_path": "/app/backend/qr_codes/user_7_xxx.png",
    "reward_points": 0
  }
}
```

---

### 3. User Authentication (QR Code Scan)
```bash
QR_CODE="c7485f5d-a1ba-4357-a1cb-c9b098180ba7"

AUTH_RESPONSE=$(curl -s -X POST http://localhost:8001/api/users/authenticate \
  -H "Content-Type: application/json" \
  -d "{\"qr_code\":\"$QR_CODE\"}")

echo $AUTH_RESPONSE

# Extract token for subsequent requests
TOKEN=$(echo $AUTH_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
```

**Expected Response:**
```json
{
  "message": "Authentication successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "Rahul Sharma",
    "phone": "9876543210",
    "reward_points": 263
  }
}
```

---

### 4. Unlock Bin (Dry Waste)
```bash
curl -X POST http://localhost:8001/api/bin/unlock \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type": "dry"}'
```

**Expected Response:**
```json
{
  "message": "Dry bin unlocked successfully",
  "waste_type": "dry",
  "user": "Rahul Sharma",
  "instruction": "Please dispose your dry waste now"
}
```

---

### 5. Unlock Bin (Wet Waste)
```bash
curl -X POST http://localhost:8001/api/bin/unlock \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type": "wet"}'
```

---

### 6. Log Waste Disposal
```bash
# Dispose 2.5 kg of dry waste
curl -X POST http://localhost:8001/api/disposal/log \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "waste_type": "dry",
    "weight": 2.5
  }'
```

**Expected Response:**
```json
{
  "message": "Disposal logged successfully",
  "disposal": {
    "id": 43,
    "waste_type": "dry",
    "weight": 2.5,
    "points_earned": 37,
    "timestamp": "2025-12-03T07:43:12"
  },
  "total_points": 300
}
```

**Reward Points Calculation:**
- Dry waste: 15 points per kg → 2.5 kg × 15 = 37 points (rounded down)
- Wet waste: 10 points per kg → 2.5 kg × 10 = 25 points

---

### 7. Get User Profile & Statistics
```bash
curl http://localhost:8001/api/users/profile \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "user": {
    "id": 1,
    "name": "Rahul Sharma",
    "phone": "9876543210",
    "address": "123 MG Road, Mumbai",
    "qr_code": "c7485f5d-a1ba-4357-a1cb-c9b098180ba7",
    "reward_points": 263,
    "created_at": "2025-12-03T07:33:52"
  },
  "statistics": {
    "total_disposals": 9,
    "total_waste_kg": 21.02,
    "dry_waste_kg": 11.43,
    "wet_waste_kg": 9.59,
    "total_redemptions": 0
  }
}
```

---

### 8. Get Available Rewards
```bash
curl http://localhost:8001/api/rewards \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "current_points": 263,
  "rewards": [
    {
      "id": 1,
      "name": "Dominos 10% Off",
      "description": "10% discount on Dominos pizza",
      "points_required": 100,
      "can_redeem": true
    },
    {
      "id": 2,
      "name": "Dominos 20% Off",
      "description": "20% discount on Dominos pizza",
      "points_required": 200,
      "can_redeem": true
    },
    {
      "id": 3,
      "name": "Dominos Free Garlic Bread",
      "description": "Free garlic bread with any pizza",
      "points_required": 150,
      "can_redeem": true
    }
  ]
}
```

---

### 9. Redeem Reward
```bash
curl -X POST http://localhost:8001/api/rewards/redeem \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"reward_id": 1}'
```

**Expected Response:**
```json
{
  "message": "Reward redeemed successfully",
  "redemption": {
    "id": 1,
    "reward_name": "Dominos 10% Off",
    "points_used": 100,
    "timestamp": "2025-12-03T07:43:21"
  },
  "remaining_points": 163
}
```

---

## ADMIN FLOW TESTS

### 1. Admin Login
```bash
ADMIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

echo $ADMIN_RESPONSE

# Extract admin token
ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
```

**Expected Response:**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "admin": {
    "id": 1,
    "username": "admin"
  }
}
```

---

### 2. Get All Users
```bash
curl http://localhost:8001/api/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
{
  "total_users": 6,
  "users": [
    {
      "id": 1,
      "name": "Rahul Sharma",
      "phone": "9876543210",
      "address": "123 MG Road, Mumbai",
      "reward_points": 163,
      "total_disposals": 9,
      "total_waste_kg": 21.02,
      "created_at": "2025-12-03T07:33:52"
    }
  ]
}
```

---

### 3. Get All Disposals (with filters)
```bash
# All disposals
curl http://localhost:8001/api/admin/disposals \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by user
curl "http://localhost:8001/api/admin/disposals?user_id=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by waste type
curl "http://localhost:8001/api/admin/disposals?waste_type=dry" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by date range
curl "http://localhost:8001/api/admin/disposals?start_date=2025-12-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
{
  "total": 42,
  "disposals": [
    {
      "id": 42,
      "user_id": 1,
      "user_name": "Rahul Sharma",
      "waste_type": "dry",
      "weight": 2.5,
      "points_earned": 37,
      "timestamp": "2025-12-03T07:43:12"
    }
  ]
}
```

---

### 4. Get Overall Statistics
```bash
curl http://localhost:8001/api/admin/statistics \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
{
  "users": {
    "total": 6
  },
  "disposals": {
    "total": 42,
    "total_waste_kg": 109.22,
    "dry_waste_kg": 39.51,
    "wet_waste_kg": 69.71
  },
  "rewards": {
    "total_points_distributed": 1271,
    "total_points_redeemed": 100,
    "total_redemptions": 1
  }
}
```

---

### 5. Get Monthly Report
```bash
# Current month (December 2025)
curl "http://localhost:8001/api/admin/reports/monthly?month=12&year=2025" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Specific month (November 2025)
curl "http://localhost:8001/api/admin/reports/monthly?month=11&year=2025" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
{
  "report": {
    "month": 12,
    "year": 2025,
    "period": "December 2025"
  },
  "summary": {
    "total_disposals": 5,
    "active_users": 4,
    "total_waste_kg": 8.39,
    "dry_waste_kg": 5.52,
    "wet_waste_kg": 2.87,
    "total_points_earned": 109,
    "total_redemptions": 1,
    "points_redeemed": 100
  },
  "top_users": [
    {
      "name": "Rahul Sharma",
      "phone": "9876543210",
      "waste_kg": 2.5
    }
  ]
}
```

---

### 6. Create New Reward
```bash
curl -X POST http://localhost:8001/api/admin/rewards \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "name": "Starbucks 15% Off",
    "description": "15% discount on Starbucks beverages",
    "points_required": 200,
    "active": true
  }'
```

**Expected Response:**
```json
{
  "message": "Reward created successfully",
  "reward": {
    "id": 6,
    "name": "Starbucks 15% Off",
    "description": "15% discount on Starbucks beverages",
    "points_required": 200,
    "active": true
  }
}
```

---

## ERROR HANDLING TESTS

### 1. Invalid QR Code
```bash
curl -X POST http://localhost:8001/api/users/authenticate \
  -H "Content-Type: application/json" \
  -d '{"qr_code": "invalid-qr-code"}'
```

**Expected:** `404 Not Found` with error message

---

### 2. Missing Token
```bash
curl -X POST http://localhost:8001/api/bin/unlock \
  -H "Content-Type: application/json" \
  -d '{"waste_type": "dry"}'
```

**Expected:** `401 Unauthorized` - Token is missing

---

### 3. Invalid Waste Type
```bash
curl -X POST http://localhost:8001/api/disposal/log \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type": "plastic", "weight": 2.0}'
```

**Expected:** `400 Bad Request` - waste_type must be 'dry' or 'wet'

---

### 4. Insufficient Points for Redemption
```bash
# Try to redeem 250-point reward with only 163 points
curl -X POST http://localhost:8001/api/rewards/redeem \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"reward_id": 5}'
```

**Expected:** `400 Bad Request` - Insufficient points

---

### 5. Duplicate Phone Registration
```bash
curl -X POST http://localhost:8001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Duplicate User",
    "phone": "9876543210",
    "address": "Any Address"
  }'
```

**Expected:** `400 Bad Request` - Phone number already registered

---

## COMPLETE END-TO-END TEST SCRIPT

Save this as `test_api.sh` and run with `bash test_api.sh`:

```bash
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
echo $REGISTER_RESPONSE | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"

NEW_QR=$(echo $REGISTER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['qr_code'])")
echo ""

# 2. Authenticate
echo "2. Authenticating user..."
AUTH_RESPONSE=$(curl -s -X POST $API_URL/users/authenticate \
  -H "Content-Type: application/json" \
  -d "{\"qr_code\":\"$NEW_QR\"}")
TOKEN=$(echo $AUTH_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
echo "Token obtained"
echo ""

# 3. Unlock dry bin
echo "3. Unlocking dry bin..."
curl -s -X POST $API_URL/bin/unlock \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type":"dry"}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# 4. Dispose waste
echo "4. Logging disposal (3 kg dry waste)..."
curl -s -X POST $API_URL/disposal/log \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"waste_type":"dry","weight":3.0}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# 5. Check profile
echo "5. Checking user profile..."
curl -s $API_URL/users/profile \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

echo "======================================"
echo "E2E TEST COMPLETED SUCCESSFULLY!"
echo "======================================"
```

---

## Notes

1. **JWT Token Expiry**: Tokens expire after 24 hours
2. **Reward Points Formula**:
   - Dry waste: 15 points per kg
   - Wet waste: 10 points per kg
3. **QR Codes**: Generated automatically during registration and stored in `/app/backend/qr_codes/`
4. **Logs**: All activities are logged to `/var/log/waste_disposal.log` and supervisor logs
