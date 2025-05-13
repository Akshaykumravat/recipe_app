cd /mnt/c/Users/AKSHAY/Desktop/PROJECT/Recipe_Maker

export FLASK_APP=run.py
export FLASK_ENV=development

flask db migrate -m "Add reset_token and reset_token_expiry to User"
flask db upgrade



flask createadmin
