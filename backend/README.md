# Smart Dual-Bin Waste Disposal Backend API

A Flask-based REST API system for managing a smart waste disposal machine with dual bins (dry/wet waste), user authentication via QR codes, reward points system, and admin panel.

## Features

- **User Management**: Register users with name, phone, and address. Generate unique QR codes for authentication.
- **QR Authentication**: Users authenticate using their unique QR code.
- **Bin Control**: API to unlock the correct bin (dry/wet) based on user selection.
- **Disposal Logging**: Log waste disposal events with user ID, waste type, timestamp, and weight.
- **Reward System**: Calculate and distribute reward points based on waste type and weight.
  - Dry waste: 15 points per kg
  - Wet waste: 10 points per kg
- **Redemption System**: Users can redeem points for rewards (e.g., Domino's 10% off).
- **Admin Panel**: Admin APIs for viewing logs, statistics, and generating reports.
- **Monthly Reports**: Generate monthly summary reports with detailed statistics.

## Project Structure

```
/app/backend/
├── server.py           # Main Flask application with all endpoints
├── database.py         # Database initialization and configuration
├── models.py           # SQLAlchemy database models
├── utils.py            # Utility functions (QR generation, points calculation)
├── requirements.txt    # Python dependencies
├── sample_data.py      # Script to populate sample test data
├── .env               # Environment variables
└── qr_codes/          # Directory for generated QR codes
```

## Database Models

### User
- id, name, phone, address, qr_code, reward_points, created_at

### Disposal
- id, user_id, waste_type, weight, points_earned, timestamp

### Reward
- id, name, description, points_required, active, created_at

### Redemption
- id, user_id, reward_id, points_used, timestamp

### Admin
- id, username, password_hash, created_at

## API Endpoints

### Public Endpoints

#### Health Check
```
GET /api/health
```

### User Endpoints

#### Register User
```
POST /api/users/register
Body: {
  "name": "John Doe",
  "phone": "9876543210",
  "address": "123 Main Street, Mumbai"
}
```

#### Authenticate User
```
POST /api/users/authenticate
Body: {
  "qr_code": "unique-qr-code-string"
}
Returns: JWT token for authenticated requests
```

#### Get User Profile
```
GET /api/users/profile
Headers: Authorization: Bearer <token>
```

#### Unlock Bin
```
POST /api/bin/unlock
Headers: Authorization: Bearer <token>
Body: {
  "waste_type": "dry"  // or "wet"
}
```

#### Log Disposal
```
POST /api/disposal/log
Headers: Authorization: Bearer <token>
Body: {
  "waste_type": "dry",  // or "wet"
  "weight": 2.5         // in kg
}
```

#### Get Available Rewards
```
GET /api/rewards
Headers: Authorization: Bearer <token>
```

#### Redeem Reward
```
POST /api/rewards/redeem
Headers: Authorization: Bearer <token>
Body: {
  "reward_id": 1
}
```

### Admin Endpoints

#### Admin Login
```
POST /api/admin/login
Body: {
  "username": "admin",
  "password": "admin123"
}
Returns: JWT token for admin requests
```

#### Get All Users
```
GET /api/admin/users
Headers: Authorization: Bearer <admin-token>
```

#### Get All Disposals
```
GET /api/admin/disposals?user_id=1&waste_type=dry&start_date=2024-01-01&end_date=2024-12-31
Headers: Authorization: Bearer <admin-token>
```

#### Get Statistics
```
GET /api/admin/statistics
Headers: Authorization: Bearer <admin-token>
```

#### Get Monthly Report
```
GET /api/admin/reports/monthly?month=1&year=2024
Headers: Authorization: Bearer <admin-token>
```

#### Create Reward
```
POST /api/admin/rewards
Headers: Authorization: Bearer <admin-token>
Body: {
  "name": "Starbucks 15% Off",
  "description": "15% discount on Starbucks",
  "points_required": 200
}
```

## Setup Instructions

### 1. Install MySQL
```bash
sudo apt-get update
sudo apt-get install mysql-server
sudo systemctl start mysql
```

### 2. Create Database
```bash
sudo mysql -u root -p
```
```sql
CREATE DATABASE waste_disposal_db;
CREATE USER 'wasteuser'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON waste_disposal_db.* TO 'wasteuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Install Dependencies
```bash
cd /app/backend
pip install -r requirements.txt
```

### 4. Configure Environment
Update `.env` file with your database credentials.

### 5. Populate Sample Data
```bash
python sample_data.py
```

### 6. Run Server
```bash
python server.py
```

The server will run on `http://0.0.0.0:8001`

## Default Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

## Default Rewards

1. Dominos 10% Off - 100 points
2. Dominos 20% Off - 200 points
3. Dominos Free Garlic Bread - 150 points
4. Swiggy 15% Off - 180 points
5. Amazon ₹50 Voucher - 250 points

## Input Validation

- All required fields are validated
- Phone numbers must be unique
- Weight must be greater than 0
- Waste type must be 'dry' or 'wet'
- Sufficient points required for redemption

## Error Handling

- All endpoints return appropriate HTTP status codes
- Detailed error messages for debugging
- Try-catch blocks for database operations
- Transaction rollback on errors

## Logging

- All important events are logged
- Logs written to `/var/log/waste_disposal.log` and console
- User registrations, authentications, disposals, and redemptions are tracked

## Security

- JWT-based authentication
- Password hashing using Werkzeug
- Separate authentication for users and admins
- Token expiration (24 hours)

## Testing

Sample curl commands are provided in the testing section below.
