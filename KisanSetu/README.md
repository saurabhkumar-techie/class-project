# 🌾 KisanSetu (किसान सेतु) - Farmer Support & Direct Marketplace

**KisanSetu** is an agricultural web platform built with Flask, designed to empower Indian farmers by connecting them directly with buyers, providing access to government schemes, agricultural guides, and support resources.

---

## 🚀 Key Features

* **🤖 Help Desk Chatbot (किसान सहायक)**: Interactive floating assistant available on every page with built-in responses about government schemes, selling and buying crops, organic farming, and support.
* **🌾 Farmer Marketplace**: List crops with quantity, quality, pricing, and unit details. Direct buyer connection with no middleman.
* **🛒 Order Management**: Buyers place orders; farmers can review, accept, or reject incoming requests. Stock updates automatically.
* **🏛️ Government Schemes**: Information on welfare programs (PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY, PKVY) with eligibility and links.
* **📚 Farmer Learning Centre**: Practical farming articles and guides in Hindi and English covering pest management, organic farming, and irrigation.
* **🔬 Crop Health Check**: Farmer-only photo upload with symptom-based, cautious crop-health guidance and pesticide safety reminders. Photos are validated for the request and are not retained by the application.
* **💬 Help & Support**: Ticketing system for farmers and buyers with direct administrative responses.
* **🛡️ Security & Role-Based Access**: Role management for Farmers, Buyers, and Admins with CSRF protection and secure password hashing.

---

## 🛠️ Technology Stack

* **Backend**: Python 3, Flask 3.1, Flask-Login, Flask-SQLAlchemy, Flask-WTF
* **Database**: SQLite (SQLAlchemy ORM)
* **Frontend**: HTML5, Jinja2, Bootstrap 5.3, Custom CSS, Vanilla JavaScript
* **Security**: CSRF Protection, Password Hashing (Werkzeug), Safe Redirect Validation

---

## 💻 Installation & Setup

Prerequisites: Python 3.10 or later and PowerShell (or another terminal).

1. **Open the project folder:**
   ```bash
   cd KisanSetu
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   In Command Prompt, activate it with `.venv\Scripts\activate.bat`.

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000/` in your browser. The app creates the `instance` directory and database tables on startup, then adds initial content when the corresponding tables are empty.

## ⚙️ Configuration

The app loads environment variables from a `.env` file in the working directory. The following settings are supported:

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session and CSRF signing key | Development-only key in `config.py` |
| `DATABASE_URL` | SQLAlchemy database connection URL | SQLite database at `instance/kisansetu.db` |
| `ADMIN_EMAIL` | Email address for the first seeded admin | `admin@kisansetu.in` |
| `ADMIN_PASSWORD` | Password for the first seeded admin | `Admin@12345` |

For local development, create a `.env` file with your own values:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
ADMIN_EMAIL=admin@kisansetu.in
ADMIN_PASSWORD=replace-with-a-unique-password
```

Set a strong, unique `SECRET_KEY` and `ADMIN_PASSWORD` before exposing the app beyond a local development environment. The admin settings only apply when an admin account is first created; changing them later does not update an existing account. Do not commit `.env` or production credentials.

## 👥 Demo Accounts and Initial Data

On a fresh database, the app seeds demo content and accounts:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@kisansetu.in` | `Admin@12345` |
| **Farmer** | `rameshwar.farmer@kisansetu.in` | `Farmer@12345` |
| **Buyer** | `buyer@kisansetu.in` | `Buyer@12345` |

The admin email and password can be changed before the first run with `ADMIN_EMAIL` and `ADMIN_PASSWORD`. The demo farmer is created when there are no crop listings and no farmer account; sample crops are then added. The demo buyer is created if no buyer account exists, along with a sample order when a crop and farmer are available.

These are public demo credentials, not private accounts. Change the admin credentials and use a non-demo database before deploying. Seed logic does not overwrite existing accounts or reset their passwords. You can also register a farmer or buyer through the site.

## 🧭 Using the Application

* **Farmers** can create and manage listings, set quantities and prices, and handle incoming order requests from their dashboard.
* **Buyers** can browse listings, request available quantities, and track their orders.
* **Admins** can review users and listings, manage schemes and articles, and respond to support requests.
* **All visitors** can browse active crop listings, schemes, and learning articles. Registered users can submit help requests; the chatbot is available throughout the site.

Order requests begin as pending. When a farmer accepts an order, the app checks and deducts the available crop quantity; a listing with no stock left is marked sold.

## 📁 Directory Overview

* `app.py` - Core routes, view controllers, role dispatchers, seed logic, `/api/chatbot`, and the crop-health upload route.
* `disease_advisory.py` - Crop and symptom guidance used by the crop-health checker.
* `models.py` - Database models (`User`, `Crop`, `Order`, `Scheme`, `Article`, `HelpRequest`).
* `forms.py` - WTForms form validation definitions.
* `config.py` - Database and application configuration.
* `templates/` - Jinja2 templates for the home page, dashboards, marketplace, schemes, articles, and support.
* `static/css/` and `static/js/` - Stylesheets and JavaScript for the interface and chatbot.
* `static/images/` - Crop images and other static image assets.
* `static/uploads/` - Uploaded crop images.
* `instance/kisansetu.db` - Default local SQLite database, created if it does not exist.

## 🔒 Development and Deployment Notes

* `python app.py` starts Flask with debug mode enabled. Use a production WSGI server and disable debug mode for deployment.
* The default secret key and seeded demo passwords are for local development only.
* The app enables CSRF protection for forms and hashes passwords before storing them. The chatbot endpoint is explicitly exempted from CSRF protection.
* Crop Health Check does not use a trained image-recognition model. Farmers select the crop and visible symptom; the app validates the uploaded photo but does not diagnose from its pixels. Treat its general guidance as preliminary, and confirm any diagnosis and pesticide choice with a local agricultural expert or KVK.
* Scheme details and chatbot replies are informational. Verify current eligibility, deadlines, and application requirements with the relevant official government source.
