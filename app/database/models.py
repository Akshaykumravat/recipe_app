from extentions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random
from datetime import timedelta, datetime


class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    verification_code_expiry = db.Column(db.DateTime, nullable=True)
    country = db.Column(db.String(20), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    def __repr__(self):
        return f"<user(user_id={self.user_id})>"

    def hash_password(self, password):
        """
        Save user's password in hash
        """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify that passwrd is correct or not
        """
        return check_password_hash(self.password, password)

    def generate_verification_code(self):
        """
        Generate a 6-digit verification code.
        """
        return ''.join(random.choices(string.digits, k=6))

    def set_verification_code(self):
        """
        Generate and store verification code and expiration time.
        """
        self.verification_code = self.generate_verification_code()
        self.verification_code_expiry = datetime.utcnow() + timedelta(minutes=2)

    def reset_verification_code(self):
        """
        Reset verification code and expiration time if expired.
        """
        self.set_verification_code()
        db.session.commit()

class Recipe(db.Model):
    __tablename__ = "recipes"
    recipe_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationship
    author = db.relationship("User", backref=db.backref("recipes", lazy=True))

    def __repr__(self):
        return f"<Recipe(recipe_id={self.recipe_id}, title={self.title})>"







