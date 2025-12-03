"""Script to populate database with sample test data"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from database import db, init_db
from models import User, Disposal, Reward, Admin
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@localhost:3306/waste_disposal_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def populate_sample_data():
    """Populate database with sample test data"""
    with app.app_context():
        print("Initializing database...")
        init_db()
        
        print("\nCreating sample users...")
        users_data = [
            {'name': 'Rahul Sharma', 'phone': '9876543210', 'address': '123 MG Road, Mumbai'},
            {'name': 'Priya Patel', 'phone': '9876543211', 'address': '456 Park Street, Delhi'},
            {'name': 'Amit Kumar', 'phone': '9876543212', 'address': '789 Brigade Road, Bangalore'},
            {'name': 'Sneha Reddy', 'phone': '9876543213', 'address': '321 Anna Salai, Chennai'},
            {'name': 'Vikram Singh', 'phone': '9876543214', 'address': '654 FC Road, Pune'},
        ]
        
        users = []
        for user_data in users_data:
            user = User(**user_data)
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        print(f"Created {len(users)} sample users")
        
        # Print user QR codes
        print("\n=== USER QR CODES ===")
        for user in users:
            print(f"User: {user.name} | Phone: {user.phone} | QR Code: {user.qr_code}")
        
        print("\nCreating sample disposal records...")
        disposals_created = 0
        
        for user in users:
            # Create 5-10 disposals per user over the last 30 days
            num_disposals = random.randint(5, 10)
            
            for i in range(num_disposals):
                waste_type = random.choice(['dry', 'wet'])
                weight = round(random.uniform(0.5, 5.0), 2)
                
                # Calculate points based on waste type
                points = int(weight * (15 if waste_type == 'dry' else 10))
                
                # Random timestamp in last 30 days
                days_ago = random.randint(0, 30)
                timestamp = datetime.utcnow() - timedelta(days=days_ago)
                
                disposal = Disposal(
                    user_id=user.id,
                    waste_type=waste_type,
                    weight=weight,
                    points_earned=points,
                    timestamp=timestamp
                )
                
                db.session.add(disposal)
                user.reward_points += points
                disposals_created += 1
        
        db.session.commit()
        print(f"Created {disposals_created} sample disposal records")
        
        print("\n=== SAMPLE DATA SUMMARY ===")
        print(f"Total Users: {User.query.count()}")
        print(f"Total Disposals: {Disposal.query.count()}")
        print(f"Total Rewards Available: {Reward.query.count()}")
        print(f"Total Admins: {Admin.query.count()}")
        
        print("\n=== DEFAULT ADMIN CREDENTIALS ===")
        print("Username: admin")
        print("Password: admin123")
        
        print("\n=== AVAILABLE REWARDS ===")
        rewards = Reward.query.all()
        for reward in rewards:
            print(f"{reward.name}: {reward.points_required} points - {reward.description}")
        
        print("\n✅ Sample data populated successfully!")

if __name__ == '__main__':
    populate_sample_data()
