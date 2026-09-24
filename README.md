# FitBuddy – AI Fitness Plan Generator using Gemini Models

FitBuddy is a production-oriented Flask web application that creates personalized fitness and general nutrition guidance with Google's Gemini API.

The application uses:

- Python
- Flask
- Jinja2
- HTML5
- CSS3
- SQLite
- SQLAlchemy
- Google Gemini API

It intentionally does **not** use React, Vue, Angular, Tailwind CSS, Bootstrap, PHP, Node.js, or MySQL.

## 1. Requirements

For Windows, install:

- Python 3.10 or newer
- A Google Gemini API key

The Gemini Python SDK currently supports Python 3.9+.

## 2. Install Python

Download Python from the official Python website and install it.

During installation on Windows, enable:

```text
Add python.exe to PATH
```

Verify PowerShell can find Python:

```powershell
python --version
```

## 3. Create a virtual environment

Open PowerShell in the FitBuddy folder:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can either use Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

or allow locally created PowerShell scripts for your user account:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

With the virtual environment active:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Get a Gemini API key

Create a Gemini API key in Google AI Studio.

Keep the key private. Do not put it in HTML, JavaScript, CSS, Git, or screenshots.

## 6. Configure environment variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Open `.env`:

```powershell
notepad .env
```

Set:

```env
SECRET_KEY=your-long-random-secret
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.8-flash
GEMINI_TIMEOUT_MS=90000
```

For a stronger secret key, generate one in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value into `SECRET_KEY`.

The `.gitignore` file excludes `.env` and the local SQLite database.

## 7. Database initialization

No manual database setup is required.

When the application starts, SQLAlchemy automatically creates:

```text
instance\fitbuddy.db
```

and creates the required tables.

## 8. Run the application

From the FitBuddy directory, with the virtual environment active:

```powershell
python app.py
```

The server listens on:

```text
http://127.0.0.1:5000
```

## 9. Open the website

Open this address in your browser:

```text
http://127.0.0.1:5000
```

Create an account, complete the fitness profile, and select **Create New Plan**.

## 10. Troubleshooting

### `SECRET_KEY is missing`

Make sure `.env` exists in the project root and contains:

```env
SECRET_KEY=some-random-secret
```

Then restart:

```powershell
python app.py
```

### Gemini says the API key is not configured

Check:

```env
GEMINI_API_KEY=your-real-key
```

Do not include quotation marks unless they are actually part of your value.

Restart the Flask process after editing `.env`.

### Gemini generation fails or times out

Check:

- Internet connection
- Gemini API key
- Gemini API availability and quota
- `GEMINI_MODEL` is a model available to your API account

You can increase the timeout in `.env`:

```env
GEMINI_TIMEOUT_MS=120000
```

Then restart the application.

### PowerShell will not activate the virtual environment

Use:

```cmd
.venv\Scripts\activate.bat
```

from Command Prompt, or set the PowerShell execution policy described above.

### Port 5000 is already in use

Stop the other process using port 5000, then run FitBuddy again.

For development only, you can change the port in `app.py`.

### The database needs to be reset

Stop the application first.

Delete:

```text
instance\fitbuddy.db
```

Then start the application again:

```powershell
python app.py
```

FitBuddy will create a new empty database automatically.

## 11. Project structure

```text
FitBuddy/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── models.py
│
├── services/
│   ├── __init__.py
│   └── gemini_service.py
│
├── routes/
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   └── fitness.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── create_plan.html
│   ├── plan.html
│   ├── history.html
│   ├── profile.html
│   └── 404.html
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── dashboard.css
│   │   └── forms.css
│   └── js/
│       └── app.js
│
└── instance/
    └── fitbuddy.db
```

## Architecture

The main AI flow is:

```text
Browser
   ↓
Flask route
   ↓
Gemini service
   ↓
Structured JSON validation
   ↓
SQLite / SQLAlchemy
   ↓
Jinja2 plan page
```

The Gemini API key remains server-side and is loaded from `.env`.

## Security notes

FitBuddy includes:

- Werkzeug password hashing
- Session-based authentication
- Server-side form validation
- CSRF tokens for state-changing forms
- Ownership filtering on plan routes
- Parameterized ORM queries
- Environment-based secrets
- No client-side Gemini API key
- Friendly error handling without debug tracebacks

For a public production deployment, also enable HTTPS and set:

```python
SESSION_COOKIE_SECURE = True
```

behind a correctly configured HTTPS deployment.

## Health and safety

FitBuddy provides AI-generated fitness and nutrition guidance for general informational purposes. It is not a substitute for professional medical or fitness advice. Consult a qualified professional if you have a medical condition, injury, or other health concern.

AI-generated guidance can be imperfect. Review recommendations critically and stop an exercise if it causes pain or feels unsafe.

## Gemini API implementation

FitBuddy uses Google's `google-genai` Python SDK and requests structured JSON from Gemini. The service validates the returned structure before storing it in SQLite.

The model is configurable through:

```env
GEMINI_MODEL=gemini-3.8-flash
```

If Google changes available model names, update this value without changing the Flask routes or templates.
