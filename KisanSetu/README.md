# 🌾 KisanSetu (किसान सेतु) - Farmer Support & Direct Marketplace

**KisanSetu** is an agricultural web platform built with Flask, designed to empower Indian farmers by connecting them directly with buyers, providing access to government schemes, agricultural guides, and support resources.

---

## 🚀 Key Features

* **🤖 24/7 AI Help Desk Chatbot (किसान सहायक)**: Interactive floating assistant available on every page to answer queries regarding government schemes, selling/buying crops, organic farming, KCC loans, and live database crop prices.
* **🌾 Farmer Marketplace**: List crops with quantity, quality, pricing, and unit details. Direct buyer connection with no middleman.
* **🛒 Order Management**: Buyers place orders; farmers can review, accept, or reject incoming requests. Stock updates automatically.
* **🏛️ Government Schemes**: Information on welfare programs (PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY, PKVY) with eligibility and links.
* **📚 Farmer Learning Centre**: Practical farming articles and guides in Hindi and English covering pest management, organic farming, and irrigation.
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

1. **Clone or open the project folder:**
   ```bash
   cd KisanSetu
   ```

2. **Activate the virtual environment:**
   ```bash
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask Application:**
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## 👥 Default Accounts (Seeded)

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@kisansetu.in` | `ChangeThisAdmin123!` |
| **Farmer** | `rameshwar.farmer@kisansetu.in` | `Farmer@12345` |
| **Buyer** | `buyer@kisansetu.in` | `Buyer@12345` |

---

## 📁 Directory Overview

* `app.py` - Core routes, view controllers, role dispatchers, seed logic, and `/api/chatbot` endpoint.
* `models.py` - Database models (`User`, `Crop`, `Order`, `Scheme`, `Article`, `HelpRequest`).
* `forms.py` - WTForms form validation definitions.
* `config.py` - Database and application configuration.
* `templates/` - Jinja2 HTML templates for all views (including floating chatbot widget).
* `static/` - Custom CSS stylesheets, JavaScript helpers, and asset directories.
