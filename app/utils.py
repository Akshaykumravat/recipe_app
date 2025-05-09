from email_validator import validate_email, EmailNotValidError
from flask_jwt_extended import create_access_token, create_refresh_token
from config import Config
from flask_mail import Message
from flask import jsonify
from flask import render_template
# from extentions import mail
import json


# from app.extensions import mail

def response(success, message, data=None, error=None):
    """
    Utility to create a consistent JSON response.

        : success: bool
        : message: str
        : data: dict or list (default: None)
        : error: str or list (default: None)

    """
    return {
        "success": success,
        "message": message,
        "data": data if data else {},
        "error": error if error else ""
    }


def is_valid_email(email):
    """
    Validate the email address using the email-validator library.
    """
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def generate_access_token_and_refresh_token(user_id, email):
    identity = json.dumps({"user_id": str(user_id), "email": email})
    tokens = {
        "access_token": create_access_token(
            identity=identity,
            additional_claims={
                "issuer_id": Config.JWT_ISSUER,
                "secret_key": Config.JWT_SECRET_KEY
            }),
        "refresh_token": create_refresh_token(
            identity=identity,
            additional_claims={
                "issuer_id": Config.JWT_ISSUER,
                "secret_key": Config.JWT_SECRET_KEY
            }),
    }
    return tokens


# def send_verification_email(user):
#     """
#     Send a verification email with a code.
#     """
#     from extentions import mail
#     msg = Message(
#         "Verify Your Email Address",
#         recipients=[user.email],
#         body=f"Your verification code is {user.verification_code}. It will expire in 2 minutes."
#     )
#     try:
#         mail.send(msg)
#     except Exception as e:
#         print(f"Error sending email: {e}")
#         return jsonify({"error": "Failed to send email"}), 500

def send_verification_email(user):
    """
    Send a verification email with a code.
    """
    from extentions import mail

    try:
        html_body = render_template('verification_email.html',
            user=user,  
            verification_code=user.verification_code,
            your_name = "Golden Recipe!!"
        )

        msg = Message("Verify Your Email Address",
            recipients=[user.email],
            html=html_body  
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"error": "Failed to send email"}), 500


def paginated_result(query, model_schema, page=1, per_page=10):

    """
    Function to handle pagination of a SQLAlchemy query.
    """
    paginated_query = query.paginate(page=page, per_page=per_page, error_out=False)  
    data = model_schema(many=True).dump(paginated_query.items)
    pagination_metadata = {
        'total': paginated_query.total,     
        'page': paginated_query.page,       
        'per_page': paginated_query.per_page,
        'pages': paginated_query.pages,     
    }
    return {
        'data': data,
        'pagination': pagination_metadata
    }


def thank_you_email(user, recipe):
    """
    Send a ThankYou email.
    """
    from extentions import mail

    try:
        print(user, "user")
        html_body = render_template('thankyou.html',
            user=user,
            recipe=recipe,
            your_name = "Golden Recipe!!"
        )

        msg = Message("Thank You for Sharing Your Recipe",
            recipients=[user.get('email')],
            html=html_body  
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"error": "Failed to send email"}), 500
    

def send_email(subject, recipients, template_name, context):
    """
    General function to send HTML emails using Flask-Mail.
    
    :param subject: Subject of the email
    :param recipients: List of recipient email addresses
    :param template_name: Name of the HTML template
    :param context: Dictionary with template variables
    :return: Flask response or None
    """
    from extentions import mail
    try:
        print(context, "context")
        html_body = render_template(template_name, **context)
        msg = Message(subject, recipients=recipients, html=html_body)
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"error": "Failed to send email"}), 500