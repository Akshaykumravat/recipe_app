# start_app.ps1

# Set environment variables
$env:DATABASE_URI="postgresql://admin:admin@localhost:5432/recipe_dev"
$env:SECRET_KEY="VoHEbTFwNK1qfYQSZ8R7yz9R5nsIKMPM"
$env:JWT_ISSUER="akshay.com"
$env:MAIL_SERVER="smtp.gmail.com"
$env:MAIL_PORT=587
$env:MAIL_USE_TLS=$true
$env:MAIL_USERNAME="akshaykumravat0701@gmail.com"
$env:MAIL_PASSWORD="mdbx qvmk kmwr tlmv"
$env:MAIL_DEFAULT_SENDER="akshaykumravat0701@gmail.com"

# Run the Flask app
# python run.py
waitress-serve --port=5000 run:app
