import json
from config import Config
from flask_mail import Message
from marshmallow import ValidationError
from flask import jsonify, render_template
from email_validator import validate_email, EmailNotValidError
from flask_jwt_extended import create_access_token, create_refresh_token


def response(success=False, message=None, data=None, error=None):
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
        "data": data if data is not None else {},
        "error": error if error is not None else {}
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
    

def validate_schema(schema, data, partial=False):
    """
    Validates input data using the given Marshmallow schema.
    Returns a tuple: (is_valid: bool, result: validated_data or error_messages)
    """
    try:
        validated_data = schema.load(data, partial=partial)
        return True, validated_data
    except ValidationError as err:
        return False, err.messages
