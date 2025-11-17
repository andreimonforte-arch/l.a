
import os
import random
import string
from datetime import datetime, timedelta
from flask import session
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

mail = Mail()


def init_mail(app):
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Your email
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Your app password
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

    mail.init_app(app)
    return mail


def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, otp_code, username):
    try:
        msg = Message(
            subject='Verify Your Email - Ma Locozz Clothing Brand',
            recipients=[email]
        )

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .otp-code {{
                    background: white;
                    border: 2px dashed #667eea;
                    padding: 20px;
                    text-align: center;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #667eea;
                    margin: 20px 0;
                    border-radius: 8px;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-size: 12px;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛍️ Ma Locozz Clothing Brand</h1>
                    <p>Email Verification</p>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Thank you for registering with Ma Locozz Clothing Brand.</p>
                    <p>To complete your registration, please use the following verification code:</p>

                    <div class="otp-code">
                        {otp_code}
                    </div>

                    <div class="warning">
                        <strong>⚠️ Important:</strong>
                        <ul>
                            <li>This code will expire in 10 minutes</li>
                            <li>Never share this code with anyone</li>
                            <li>If you didn't request this code, please ignore this email</li>
                        </ul>
                    </div>

                    <p>If you have any questions, please contact our support team.</p>
                    <p>Best regards,<br><strong>Ma Locozz Team</strong></p>
                </div>
                <div class="footer">
                    <p>© 2025 Ma Locozz Clothing Brand. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.body = f"""
        Ma Locozz Clothing Brand - Email Verification

        Hello {username}!

        Thank you for registering with Ma Locozz Clothing Brand.

        Your verification code is: {otp_code}

        This code will expire in 10 minutes.
        Never share this code with anyone.

        If you didn't request this code, please ignore this email.

        Best regards,
        Ma Locozz Team
        """

        mail.send(msg)
        return True

    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False


def store_otp_in_session(email, otp_code):
    session['otp_email'] = email
    session['otp_code'] = otp_code
    session['otp_expires'] = (datetime.now() + timedelta(minutes=10)).isoformat()
    session['otp_attempts'] = 0


def verify_otp(email, entered_otp):

    if 'otp_email' not in session or 'otp_code' not in session:
        return False, "No OTP found. Please request a new code."

    if session.get('otp_email') != email:
        return False, "Email mismatch. Please try again."

    if datetime.now() > datetime.fromisoformat(session.get('otp_expires')):
        clear_otp_session()
        return False, "OTP has expired. Please request a new code."

    attempts = session.get('otp_attempts', 0)
    if attempts >= 5:
        clear_otp_session()
        return False, "Too many failed attempts. Please request a new code."

    if session.get('otp_code') == entered_otp:
        clear_otp_session()
        return True, "Email verified successfully!"
    else:
        session['otp_attempts'] = attempts + 1
        remaining = 5 - session['otp_attempts']
        return False, f"Invalid OTP. {remaining} attempts remaining."


def clear_otp_session():
    session.pop('otp_email', None)
    session.pop('otp_code', None)
    session.pop('otp_expires', None)
    session.pop('otp_attempts', None)


def setup_otp_routes(app):

    @app.route('/send-otp', methods=['POST'])
    def send_otp():
        from flask import request, jsonify

        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()

        if not email or '@' not in email:
            return jsonify({'success': False, 'message': 'Invalid email address'}), 400

        otp_code = generate_otp()

        if send_otp_email(email, otp_code, username):
            store_otp_in_session(email, otp_code)
            return jsonify({'success': True, 'message': 'OTP sent to your email'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP. Please try again.'}), 500

    @app.route('/verify-otp', methods=['POST'])
    def verify_otp_route():
        from flask import request, jsonify

        email = request.form.get('email', '').strip()
        otp = request.form.get('otp', '').strip()

        success, message = verify_otp(email, otp)

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400