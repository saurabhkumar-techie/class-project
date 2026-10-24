
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    FloatField,
    TextAreaField,
    IntegerField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    URL,
)


class RegistrationForm(FlaskForm):
    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match.")
        ]
    )
    role = SelectField(
        "Register As",
        choices=[
            ("farmer", "Farmer"),
            ("buyer", "Buyer"),
        ],
        validators=[DataRequired()]
    )
    phone = StringField("Phone Number", validators=[Optional(), Length(max=20)])
    village = StringField("Village", validators=[Optional(), Length(max=100)])
    district = StringField("District", validators=[Optional(), Length(max=100)])
    state = StringField("State", validators=[Optional(), Length(max=100)])
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )
    submit = SubmitField("Login")


class CropForm(FlaskForm):
    name = StringField(
        "Crop Name",
        validators=[DataRequired(), Length(max=100)]
    )
    quantity = FloatField(
        "Available Quantity",
        validators=[DataRequired(), NumberRange(min=0.01)]
    )
    unit = SelectField(
        "Unit",
        choices=[
            ("kg", "Kilograms (kg)"),
            ("quintal", "Quintal"),
            ("ton", "Ton"),
        ],
        validators=[DataRequired()]
    )
    price_per_unit = FloatField(
        "Price Per Unit (₹)",
        validators=[DataRequired(), NumberRange(min=0.01)]
    )
    quality = SelectField(
        "Crop Quality",
        choices=[
            ("Standard", "Standard"),
            ("Good", "Good"),
            ("Premium", "Premium"),
        ],
        validators=[Optional()]
    )
    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=2000)]
    )
    submit = SubmitField("Save Crop")


class OrderForm(FlaskForm):
    quantity = FloatField(
        "Required Quantity",
        validators=[DataRequired(), NumberRange(min=0.01)]
    )
    submit = SubmitField("Place Order Request")


class HelpRequestForm(FlaskForm):
    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(min=3, max=200)]
    )
    category = SelectField(
        "Help Category",
        choices=[
            ("crop", "Crop Related"),
            ("market", "Market and Pricing"),
            ("scheme", "Government Schemes"),
            ("account", "Account Related"),
            ("other", "Other"),
        ],
        validators=[DataRequired()]
    )
    description = TextAreaField(
        "Describe Your Problem",
        validators=[DataRequired(), Length(min=10, max=3000)]
    )
    submit = SubmitField("Submit Help Request")


class SchemeForm(FlaskForm):
    name = StringField(
        "Scheme Name",
        validators=[DataRequired(), Length(max=200)]
    )
    description = TextAreaField(
        "Description",
        validators=[DataRequired()]
    )
    eligibility = TextAreaField("Eligibility", validators=[Optional()])
    documents = TextAreaField("Required Documents", validators=[Optional()])
    application_steps = TextAreaField(
        "Application Steps",
        validators=[Optional()]
    )
    official_url = StringField(
        "Official Website URL",
        validators=[Optional(), URL()]
    )
    submit = SubmitField("Save Scheme")


class ArticleForm(FlaskForm):
    title = StringField(
        "Article Title",
        validators=[DataRequired(), Length(max=200)]
    )
    category = StringField(
        "Category",
        validators=[Optional(), Length(max=100)]
    )
    content = TextAreaField(
        "Article Content",
        validators=[DataRequired()]
    )
    language = SelectField(
        "Language",
        choices=[
            ("Hindi", "Hindi"),
            ("English", "English"),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Save Article")


class AdminResponseForm(FlaskForm):
    status = SelectField(
        "Request Status",
        choices=[
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
        ],
        validators=[DataRequired()]
    )
    admin_response = TextAreaField(
        "Admin Response",
        validators=[Optional(), Length(max=3000)]
    )
    submit = SubmitField("Update Request")
