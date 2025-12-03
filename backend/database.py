from flask_sqlalchemy import SQLAlchemy
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()

def init_db():
    """Initialize database and create tables"""
    try:
        db.create_all()
        
        # Import models here to avoid circular import
        from models import Admin, Reward
        from werkzeug.security import generate_password_hash
        
        # Create default admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            default_admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(default_admin)
            logger.info("Default admin created: username='admin', password='admin123'")
        
        # Create default rewards if not exist
        default_rewards = [
            {'name': 'Dominos 10% Off', 'description': '10% discount on Dominos pizza', 'points_required': 100},
            {'name': 'Dominos 20% Off', 'description': '20% discount on Dominos pizza', 'points_required': 200},
            {'name': 'Dominos Free Garlic Bread', 'description': 'Free garlic bread with any pizza', 'points_required': 150},
            {'name': 'Swiggy 15% Off', 'description': '15% discount on Swiggy orders', 'points_required': 180},
            {'name': 'Amazon ₹50 Voucher', 'description': '₹50 Amazon gift voucher', 'points_required': 250},
        ]
        
        for reward_data in default_rewards:
            if not Reward.query.filter_by(name=reward_data['name']).first():
                reward = Reward(**reward_data)
                db.session.add(reward)
                logger.info(f"Default reward created: {reward_data['name']}")
        
        db.session.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing database: {str(e)}")
        raise
