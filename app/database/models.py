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
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
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

class RecipeCategories(db.Model):
    __tablename__ = "recipe_categories"
    
    category_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # No direct relationships needed here unless needed for admin tracking

    def __repr__(self):
        return f"<RecipeCategories(category_id={self.category_id}, name={self.category_name})>"


class Recipe(db.Model):
    __tablename__ = "recipes"
    
    recipe_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"), nullable=False)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey("recipe_categories.category_id"), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    author = db.relationship("User", backref=db.backref("recipes", lazy=True))
    category = db.relationship("RecipeCategories", backref=db.backref("recipes", lazy=True))

    def __repr__(self):
        return f"<Recipe(recipe_id={self.recipe_id}, title={self.title})>"

    
class Favorites(db.Model):
    __tablename__ = "favorites"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    recipe_id = db.Column(UUID(as_uuid=True), db.ForeignKey("recipes.recipe_id"), nullable=False) 
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"), nullable=False) 
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())  

    # Relationships
    recipe = db.relationship("Recipe", backref=db.backref("favorites", lazy=True)) 
    user = db.relationship("User", backref=db.backref("favorites", lazy=True))  

    def __repr__(self):
        return f"<Favorites(id={self.id})>"
    

class Comments (db.Model):
    __tablename__ = "comments"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    recipe_id = db.Column(UUID(as_uuid=True), db.ForeignKey("recipes.recipe_id"), nullable=False) 
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"), nullable=False) 
    Comment = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())  

    # Relationships
    recipe = db.relationship("Recipe", backref=db.backref("comments", lazy=True)) 
    user = db.relationship("User", backref=db.backref("comments", lazy=True))  

    def __repr__(self):
        return f"<Comments(id={self.id})>"








