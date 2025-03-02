import tempfile

from flask_restx import Api

from geodata import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)