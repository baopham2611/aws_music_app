# ./frontend/app.py
from dotenv import load_dotenv
load_dotenv()  

from application import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=app.config['DEBUG'], port=int(app.config['PORT']))

