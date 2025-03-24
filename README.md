# PWP SPRING 2025

# Crowdsourced Local insights API

# Group information

- Mohammad Abaeiani, [Mohammad.Abaeiani@student.oulu.fi](mailto:Mohammad.Abaeiani@student.oulu.fi)
- Xiru Chen, [Xiru.Chen@student.oulu.fi](mailto:Xiru.Chen@student.oulu.fi)
- Touko Kinnunen. [Touko.Kinnunen@student.oulu.fi](mailto:Touko.Kinnunen@student.oulu.fi)

---

## Usage

This section explains how to get the project up and running on your local machine. For database we are using SQLite version 3.43.2

### 1. Clone the Repository

Clone the project repository from GitHub:

```bash
git clone https://github.com/MagusDev/Crowdsourced-Local-Insights.git
cd Crowdsourced-Local-Insights
```

### 2. (Optional) Create and Activate a Virtual Environment

Using a virtual environment is optional but recommended to isolate the project dependencies.

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

Install the required dependencies using requirements.txt:

```bash
pip install -r requirements.txt
```

### 5. Prepopulate Database

To populate the database run file test_database.py

```bash
python test_database.py
```

### 6. Running the API

#### Method 1

run the app directlyby running the run.py file

```bash
python run.py
```

#### Method 2

To run the API run the following command to install the package

```bash
pip install -e .
```

Then setup flash environment variables

```bash
# Windows
set FLASK_APP=geodata
set FLASK_ENV=development

# Linux/macOS
export FLASK_APP=geodata
export FLASK_ENV=development
```

Run the application:

```bash
flask run
```

the application will be available at http://127.0.0.1:5000/

### 7. Running the tests

The tests are available at Test directory. You can tests for all the resources implemented by

```bash
pytest --cov=geodata.resources --cov-report=term-missing Test/test_resources.py
```

This command also shows the test covarage in tests

the errors solved by tests:

1. Converter configrations for long urls
2. Integrity errors for put commands
3. Authentication issues for users
