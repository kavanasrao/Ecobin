from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import jwt
from functools import wraps
import hashlib

# Import database and models
from database import db, init_db
from models import User, Disposal, Reward, Redemption, Admin
from utils import generate_qr_code, calculate_reward_points

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/waste_disposal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Authentication decorator for users
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Authentication decorator for admins
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_admin = Admin.query.get(data['admin_id'])
            if not current_admin:
                return jsonify({'error': 'Admin not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_admin, *args, **kwargs)
    return decorated

# ==================== USER ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Smart Waste Disposal API is running'}), 200

@app.route('/api/users/register', methods=['POST'])
def register_user():
    """Register a new user and generate QR code"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'phone', 'address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if phone already exists
        if User.query.filter_by(phone=data['phone']).first():
            return jsonify({'error': 'Phone number already registered'}), 400
        
        # Create new user
        user = User(
            name=data['name'],
            phone=data['phone'],
            address=data['address']
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate QR code
        qr_code_path = generate_qr_code(user.qr_code, user.id)
        
        logger.info(f"New user registered: {user.name} (ID: {user.id})")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'qr_code': user.qr_code,
                'qr_code_path': qr_code_path,
                'reward_points': user.reward_points
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/authenticate', methods=['POST'])
def authenticate_user():
    """Authenticate user with QR code"""
    try:
        data = request.get_json()
        
        if not data.get('qr_code'):
            return jsonify({'error': 'QR code is required'}), 400
        
        user = User.query.filter_by(qr_code=data['qr_code']).first()
        
        if not user:
            return jsonify({'error': 'Invalid QR code'}), 404
        
        # Generate JWT token
        token = jwt.encode(
            {
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        logger.info(f"User authenticated: {user.name} (ID: {user.id})")
        
        return jsonify({
            'message': 'Authentication successful',
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'reward_points': user.reward_points
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/bin/unlock', methods=['POST'])
@token_required
def unlock_bin(current_user):
    """Unlock the correct bin based on waste type"""
    try:
        data = request.get_json()
        
        if not data.get('waste_type'):
            return jsonify({'error': 'waste_type is required'}), 400
        
        waste_type = data['waste_type'].lower()
        
        if waste_type not in ['dry', 'wet']:
            return jsonify({'error': 'waste_type must be either "dry" or "wet"'}), 400
        
        logger.info(f"Bin unlock requested by {current_user.name} for {waste_type} waste")
        
        return jsonify({
            'message': f'{waste_type.capitalize()} bin unlocked successfully',
            'waste_type': waste_type,
            'user': current_user.name,
            'instruction': f'Please dispose your {waste_type} waste now'
        }), 200
    
    except Exception as e:
        logger.error(f"Error unlocking bin: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/disposal/log', methods=['POST'])
@token_required
def log_disposal(current_user):
    """Log waste disposal event and calculate rewards"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('waste_type'):
            return jsonify({'error': 'waste_type is required'}), 400
        if not data.get('weight'):
            return jsonify({'error': 'weight is required'}), 400
        
        waste_type = data['waste_type'].lower()
        weight = float(data['weight'])
        
        if waste_type not in ['dry', 'wet']:
            return jsonify({'error': 'waste_type must be either "dry" or "wet"'}), 400
        
        if weight <= 0:
            return jsonify({'error': 'weight must be greater than 0'}), 400
        
        # Calculate reward points
        points_earned = calculate_reward_points(waste_type, weight)
        
        # Create disposal record
        disposal = Disposal(
            user_id=current_user.id,
            waste_type=waste_type,
            weight=weight,
            points_earned=points_earned
        )
        
        # Update user reward points
        current_user.reward_points += points_earned
        
        db.session.add(disposal)
        db.session.commit()
        
        logger.info(f"Disposal logged: User {current_user.name}, {waste_type} waste, {weight}kg, {points_earned} points")
        
        return jsonify({
            'message': 'Disposal logged successfully',
            'disposal': {
                'id': disposal.id,
                'waste_type': disposal.waste_type,
                'weight': disposal.weight,
                'points_earned': disposal.points_earned,
                'timestamp': disposal.timestamp.isoformat()
            },
            'total_points': current_user.reward_points
        }), 201
    
    except ValueError:
        return jsonify({'error': 'Invalid weight value'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging disposal: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/profile', methods=['GET'])
@token_required
def get_user_profile(current_user):
    """Get user profile and statistics"""
    try:
        disposals = Disposal.query.filter_by(user_id=current_user.id).all()
        redemptions = Redemption.query.filter_by(user_id=current_user.id).all()
        
        total_waste = sum(d.weight for d in disposals)
        dry_waste = sum(d.weight for d in disposals if d.waste_type == 'dry')
        wet_waste = sum(d.weight for d in disposals if d.waste_type == 'wet')
        
        return jsonify({
            'user': {
                'id': current_user.id,
                'name': current_user.name,
                'phone': current_user.phone,
                'address': current_user.address,
                'qr_code': current_user.qr_code,
                'reward_points': current_user.reward_points,
                'created_at': current_user.created_at.isoformat()
            },
            'statistics': {
                'total_disposals': len(disposals),
                'total_waste_kg': round(total_waste, 2),
                'dry_waste_kg': round(dry_waste, 2),
                'wet_waste_kg': round(wet_waste, 2),
                'total_redemptions': len(redemptions)
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/rewards', methods=['GET'])
@token_required
def get_available_rewards(current_user):
    """Get available rewards for redemption"""
    try:
        rewards = Reward.query.filter_by(active=True).all()
        
        reward_list = [{
            'id': r.id,
            'name': r.name,
            'description': r.description,
            'points_required': r.points_required,
            'can_redeem': current_user.reward_points >= r.points_required
        } for r in rewards]
        
        return jsonify({
            'current_points': current_user.reward_points,
            'rewards': reward_list
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching rewards: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/rewards/redeem', methods=['POST'])
@token_required
def redeem_reward(current_user):
    """Redeem a reward"""
    try:
        data = request.get_json()
        
        if not data.get('reward_id'):
            return jsonify({'error': 'reward_id is required'}), 400
        
        reward = Reward.query.get(data['reward_id'])
        
        if not reward:
            return jsonify({'error': 'Reward not found'}), 404
        
        if not reward.active:
            return jsonify({'error': 'Reward is not available'}), 400
        
        if current_user.reward_points < reward.points_required:
            return jsonify({'error': 'Insufficient points'}), 400
        
        # Create redemption record
        redemption = Redemption(
            user_id=current_user.id,
            reward_id=reward.id,
            points_used=reward.points_required
        )
        
        # Deduct points from user
        current_user.reward_points -= reward.points_required
        
        db.session.add(redemption)
        db.session.commit()
        
        logger.info(f"Reward redeemed: User {current_user.name}, Reward {reward.name}")
        
        return jsonify({
            'message': 'Reward redeemed successfully',
            'redemption': {
                'id': redemption.id,
                'reward_name': reward.name,
                'points_used': redemption.points_used,
                'timestamp': redemption.timestamp.isoformat()
            },
            'remaining_points': current_user.reward_points
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error redeeming reward: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# ==================== ADMIN ENDPOINTS ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        admin = Admin.query.filter_by(username=data['username']).first()
        
        if not admin or not admin.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode(
            {
                'admin_id': admin.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        logger.info(f"Admin logged in: {admin.username}")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'admin': {
                'id': admin.id,
                'username': admin.username
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error during admin login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users(current_admin):
    """Get all users with their statistics"""
    try:
        users = User.query.all()
        
        user_list = []
        for user in users:
            disposals = Disposal.query.filter_by(user_id=user.id).all()
            total_waste = sum(d.weight for d in disposals)
            
            user_list.append({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'address': user.address,
                'reward_points': user.reward_points,
                'total_disposals': len(disposals),
                'total_waste_kg': round(total_waste, 2),
                'created_at': user.created_at.isoformat()
            })
        
        return jsonify({'users': user_list, 'total_users': len(user_list)}), 200
    
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/disposals', methods=['GET'])
@admin_required
def get_all_disposals(current_admin):
    """Get all disposal logs with filters"""
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        waste_type = request.args.get('waste_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Disposal.query
        
        # Apply filters
        if user_id:
            query = query.filter_by(user_id=user_id)
        if waste_type:
            query = query.filter_by(waste_type=waste_type.lower())
        if start_date:
            query = query.filter(Disposal.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Disposal.timestamp <= datetime.fromisoformat(end_date))
        
        disposals = query.order_by(Disposal.timestamp.desc()).all()
        
        disposal_list = []
        for disposal in disposals:
            user = User.query.get(disposal.user_id)
            disposal_list.append({
                'id': disposal.id,
                'user_id': disposal.user_id,
                'user_name': user.name if user else 'Unknown',
                'waste_type': disposal.waste_type,
                'weight': disposal.weight,
                'points_earned': disposal.points_earned,
                'timestamp': disposal.timestamp.isoformat()
            })
        
        return jsonify({'disposals': disposal_list, 'total': len(disposal_list)}), 200
    
    except Exception as e:
        logger.error(f"Error fetching disposals: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/statistics', methods=['GET'])
@admin_required
def get_statistics(current_admin):
    """Get overall waste collection statistics"""
    try:
        total_users = User.query.count()
        total_disposals = Disposal.query.count()
        
        all_disposals = Disposal.query.all()
        total_waste = sum(d.weight for d in all_disposals)
        dry_waste = sum(d.weight for d in all_disposals if d.waste_type == 'dry')
        wet_waste = sum(d.weight for d in all_disposals if d.waste_type == 'wet')
        total_points_distributed = sum(d.points_earned for d in all_disposals)
        
        total_redemptions = Redemption.query.count()
        total_points_redeemed = sum(r.points_used for r in Redemption.query.all())
        
        return jsonify({
            'users': {
                'total': total_users
            },
            'disposals': {
                'total': total_disposals,
                'total_waste_kg': round(total_waste, 2),
                'dry_waste_kg': round(dry_waste, 2),
                'wet_waste_kg': round(wet_waste, 2)
            },
            'rewards': {
                'total_points_distributed': total_points_distributed,
                'total_points_redeemed': total_points_redeemed,
                'total_redemptions': total_redemptions
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/reports/monthly', methods=['GET'])
@admin_required
def get_monthly_report(current_admin):
    """Generate monthly summary report"""
    try:
        # Get month and year from query params, default to current month
        month = request.args.get('month', type=int, default=datetime.now().month)
        year = request.args.get('year', type=int, default=datetime.now().year)
        
        # Validate month and year
        if month < 1 or month > 12:
            return jsonify({'error': 'Invalid month (1-12)'}), 400
        if year < 2000 or year > 2100:
            return jsonify({'error': 'Invalid year'}), 400
        
        # Calculate date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Query disposals for the month
        disposals = Disposal.query.filter(
            Disposal.timestamp >= start_date,
            Disposal.timestamp < end_date
        ).all()
        
        # Calculate statistics
        total_waste = sum(d.weight for d in disposals)
        dry_waste = sum(d.weight for d in disposals if d.waste_type == 'dry')
        wet_waste = sum(d.weight for d in disposals if d.waste_type == 'wet')
        total_points = sum(d.points_earned for d in disposals)
        
        # Get unique users who disposed in this month
        unique_users = len(set(d.user_id for d in disposals))
        
        # Get redemptions for the month
        redemptions = Redemption.query.filter(
            Redemption.timestamp >= start_date,
            Redemption.timestamp < end_date
        ).all()
        
        # Top users by waste disposed
        user_waste = {}
        for disposal in disposals:
            if disposal.user_id not in user_waste:
                user_waste[disposal.user_id] = 0
            user_waste[disposal.user_id] += disposal.weight
        
        top_users = []
        for user_id, waste in sorted(user_waste.items(), key=lambda x: x[1], reverse=True)[:5]:
            user = User.query.get(user_id)
            if user:
                top_users.append({
                    'name': user.name,
                    'phone': user.phone,
                    'waste_kg': round(waste, 2)
                })
        
        return jsonify({
            'report': {
                'month': month,
                'year': year,
                'period': f"{start_date.strftime('%B %Y')}"
            },
            'summary': {
                'total_disposals': len(disposals),
                'active_users': unique_users,
                'total_waste_kg': round(total_waste, 2),
                'dry_waste_kg': round(dry_waste, 2),
                'wet_waste_kg': round(wet_waste, 2),
                'total_points_earned': total_points,
                'total_redemptions': len(redemptions),
                'points_redeemed': sum(r.points_used for r in redemptions)
            },
            'top_users': top_users
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/rewards', methods=['POST'])
@admin_required
def create_reward(current_admin):
    """Create a new reward"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description', 'points_required']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        reward = Reward(
            name=data['name'],
            description=data['description'],
            points_required=int(data['points_required']),
            active=data.get('active', True)
        )
        
        db.session.add(reward)
        db.session.commit()
        
        logger.info(f"New reward created by {current_admin.username}: {reward.name}")
        
        return jsonify({
            'message': 'Reward created successfully',
            'reward': {
                'id': reward.id,
                'name': reward.name,
                'description': reward.description,
                'points_required': reward.points_required,
                'active': reward.active
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating reward: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Initialize database on startup
with app.app_context():
    init_db()

# For ASGI server compatibility (uvicorn)
from asgiref.wsgi import WsgiToAsgi
app_asgi = WsgiToAsgi(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=False)
