# Install flask so this can work for both of us
# use flask run when you want to run the file
from flask import Flask

app = Flask(__name__)

@app.route('/favorite/<int:post_id>', methods=['POST'])

def favorites():
    pass