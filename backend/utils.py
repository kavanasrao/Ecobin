import qrcode
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Reward points configuration
REWARD_CONFIG = {
    'dry': 15,  # 15 points per kg for dry waste
    'wet': 10   # 10 points per kg for wet waste
}

def generate_qr_code(qr_data, user_id):
    """Generate QR code for user authentication"""
    try:
        # Create QR code directory if it doesn't exist
        qr_dir = Path('/app/backend/qr_codes')
        qr_dir.mkdir(exist_ok=True)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_filename = f'user_{user_id}_{qr_data}.png'
        qr_path = qr_dir / qr_filename
        img.save(qr_path)
        
        logger.info(f"QR code generated: {qr_path}")
        return str(qr_path)
    
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None

def calculate_reward_points(waste_type, weight):
    """Calculate reward points based on waste type and weight"""
    points_per_kg = REWARD_CONFIG.get(waste_type.lower(), 0)
    return int(weight * points_per_kg)
