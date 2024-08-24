To run the app 
Initialize the aws environment first:

aws configuration

CD to backend folder run: nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
--> Install the requirement libraries

CD to frontend folder and run: nohup python app.py > frontend.log 2>&1 &
--> Install the requirement libraries
 
