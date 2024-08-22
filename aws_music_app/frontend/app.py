# ./frontend/app.py
from dotenv import load_dotenv
load_dotenv()  

from application import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'], port=int(app.config['PORT']))

