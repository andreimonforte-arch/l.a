from flask import Flask, request, jsonify
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import re

app = Flask(__name__)

GMAIL_USER = 'andreimonforte@gmail.com'
GMAIL_APP_PASSWORD = 'YOUR_APP_PASSWORD_HERE'  # Get from Google Account settings

otp_store = {}


def send_email_smtp(to_email, subject, body):
    try:
        message = MIMEMultipart()
        message['From'] = GMAIL_USER
        message['To'] = to_email
        message['Subject'] = subject

        message.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

        text = message.as_string()
        server.sendmail(GMAIL_USER, to_email, text)
        server.quit()

        return True, "Email sent successfully"

    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Please check your email and app password."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


@app.route('/send_otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        otp = random.randint(100000, 999999)

        expiration_time = datetime.now() + timedelta(minutes=10)
        otp_store[email] = {
            'otp': otp,
            'expires_at': expiration_time
        }

        subject = 'Your OTP Code - Ma Locozz Clothing Inventory'
        body = f'''Hello,

Your One-Time Password (OTP) for Ma Locozz Clothing Inventory registration is:

{otp}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
Ma Locozz Clothing Team
'''

        success, message = send_email_smtp(email, subject, body)

        if success:
            print(f"[DEBUG] OTP sent to {email}: {otp}")
            print(f"[DEBUG] Expires at: {expiration_time.strftime('%Y-%m-%d %H-%M-%S')}")

            return jsonify({
                'success': True,
                'message': 'OTP sent successfully',
                'debug_otp': otp  # Remove this in production!
            })
        else:
            print(f"[ERROR] {message}")
            return jsonify({
                'success': False,
                'message': message
            }), 500

    except Exception as e:
        print(f"[ERROR] Failed to send OTP: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'message': 'Failed to send OTP. Please try again.',
            'error': str(e)
        }), 500


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        otp_entered = data.get('otp')

        if not email or not otp_entered:
            return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400

        if email not in otp_store:
            return jsonify({'success': False, 'message': 'No OTP found. Please request a new one.'}), 400

        stored_data = otp_store[email]
        stored_otp = stored_data['otp']
        expires_at = stored_data['expires_at']

        if datetime.now() > expires_at:
            del otp_store[email]  # Remove expired OTP
            return jsonify({'success': False, 'message': 'OTP has expired. Please request a new one.'}), 400

        if str(otp_entered) == str(stored_otp):
            del otp_store[email]
            return jsonify({'success': True, 'message': 'OTP verified successfully'})
        else:
            return jsonify({'success': False, 'message': 'Invalid OTP. Please try again.'}), 400

    except Exception as e:
        print(f"[ERROR] OTP verification failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Verification failed'}), 500

def cleanup_expired_otps():
    current_time = datetime.now()
    expired_emails = [
        email for email, data in otp_store.items()
        if current_time > data['expires_at']
    ]

    for email in expired_emails:
        del otp_store[email]
        print(f"[CLEANUP] Removed expired OTP for {email}")


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 50)
    print(f"Gmail User: {GMAIL_USER}")
    print(f"App Password Set: {'Yes' if GMAIL_APP_PASSWORD != 'YOUR_APP_PASSWORD_HERE' else 'No - PLEASE UPDATE!'}")
    print("=" * 50 + "\n")

    app.run(debug=True, port=5000)