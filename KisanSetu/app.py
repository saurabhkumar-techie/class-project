
import io
import os
from datetime import datetime, timezone
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_wtf.csrf import CSRFProtect
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_

from config import Config
from disease_advisory import CROPS, SYMPTOMS, get_advisory
from models import (
    db,
    User,
    Crop,
    Order,
    Negotiation,
    NegotiationMessage,
    Scheme,
    Article,
    HelpRequest,
)
from forms import (
    RegistrationForm,
    LoginForm,
    CropForm,
    OrderForm,
    NegotiationOfferForm,
    NegotiationReplyForm,
    HelpRequestForm,
    SchemeForm,
    ArticleForm,
    AdminResponseForm,
)

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."

MAX_DISEASE_IMAGE_BYTES = 5 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_DISEASE_IMAGE_BYTES + 64 * 1024


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def role_required(*roles):
    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


# -------------------- HOME --------------------

@app.route("/")
def index():
    crops = Crop.query.filter_by(status="active").order_by(
        Crop.created_at.desc()
    ).limit(6).all()

    schemes = Scheme.query.filter_by(is_active=True).order_by(
        Scheme.created_at.desc()
    ).limit(3).all()

    return render_template(
        "index.html",
        crops=crops,
        schemes=schemes,
    )


# -------------------- AUTHENTICATION --------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegistrationForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
        else:
            user = User(
                name=form.name.data.strip(),
                email=email,
                role=form.role.data,
                phone=form.phone.data,
                village=form.village.data,
                district=form.district.data,
                state=form.state.data,
            )

            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            flash(
                "Account created successfully. Please log in.",
                "success",
            )
            return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Welcome back!", "success")

            next_page = request.args.get("next", "")

            # Allow only local paths for redirects.
            if (
                next_page.startswith("/")
                and not next_page.startswith("//")
                and "\\" not in next_page
            ):
                return redirect(next_page)

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "farmer":
        return redirect(url_for("farmer_dashboard"))

    if current_user.role == "buyer":
        return redirect(url_for("buyer_dashboard"))

    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    abort(403)


# -------------------- FARMER DASHBOARD --------------------

@app.route("/farmer/dashboard")
@role_required("farmer")
def farmer_dashboard():
    crops = Crop.query.filter_by(
        farmer_id=current_user.id
    ).order_by(
        Crop.created_at.desc()
    ).limit(5).all()

    orders = Order.query.filter_by(
        farmer_id=current_user.id
    ).order_by(
        Order.created_at.desc()
    ).limit(5).all()

    crop_count = Crop.query.filter_by(
        farmer_id=current_user.id
    ).count()

    pending_count = Order.query.filter_by(
        farmer_id=current_user.id,
        status="pending",
    ).count()

    return render_template(
        "farmer_dashboard.html",
        crops=crops,
        orders=orders,
        crop_count=crop_count,
        pending_count=pending_count,
    )


# -------------------- BUYER DASHBOARD --------------------

@app.route("/buyer/dashboard")
@role_required("buyer")
def buyer_dashboard():
    crops = Crop.query.filter_by(status="active").order_by(
        Crop.created_at.desc()
    ).limit(6).all()

    orders = Order.query.filter_by(
        buyer_id=current_user.id
    ).order_by(
        Order.created_at.desc()
    ).limit(5).all()

    return render_template(
        "buyer_dashboard.html",
        crops=crops,
        orders=orders,
    )


# -------------------- ADMIN DASHBOARD --------------------

@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    user_count = User.query.count()
    crop_count = Crop.query.count()
    order_count = Order.query.count()

    pending_help_count = HelpRequest.query.filter(
        HelpRequest.status != "resolved"
    ).count()

    recent_users = User.query.order_by(
        User.created_at.desc()
    ).limit(5).all()

    recent_crops = Crop.query.order_by(
        Crop.created_at.desc()
    ).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        user_count=user_count,
        crop_count=crop_count,
        order_count=order_count,
        pending_help_count=pending_help_count,
        recent_users=recent_users,
        recent_crops=recent_crops,
    )


# -------------------- CROP LIST AND SEARCH --------------------

@app.route("/crops")
def crop_list():
    search = request.args.get("q", "").strip()
    sort = request.args.get("sort", "newest")

    query = Crop.query.filter_by(status="active")

    if search:
        query = query.filter(
            or_(
                Crop.name.ilike(f"%{search}%"),
                Crop.description.ilike(f"%{search}%"),
            )
        )

    if sort == "price_low":
        query = query.order_by(Crop.price_per_unit.asc())
    elif sort == "price_high":
        query = query.order_by(Crop.price_per_unit.desc())
    elif sort == "name":
        query = query.order_by(Crop.name.asc())
    else:
        query = query.order_by(Crop.created_at.desc())

    crops = query.all()

    return render_template(
        "crop_list.html",
        crops=crops,
        search=search,
        sort=sort,
    )


@app.route("/crops/<int:crop_id>")
def crop_detail(crop_id):
    crop = db.get_or_404(Crop, crop_id)

    if crop.status != "active":
        can_view = (
            current_user.is_authenticated
            and (
                current_user.role == "admin"
                or (
                    current_user.role == "farmer"
                    and crop.farmer_id == current_user.id
                )
            )
        )

        if not can_view:
            abort(404)

    form = OrderForm()
    negotiation_form = NegotiationOfferForm()

    return render_template(
        "crop_detail.html",
        crop=crop,
        form=form,
        negotiation_form=negotiation_form,
    )


@app.route("/crops/add", methods=["GET", "POST"])
@role_required("farmer")
def add_crop():
    form = CropForm()

    if form.validate_on_submit():
        crop = Crop(
            farmer_id=current_user.id,
            name=form.name.data.strip(),
            quantity=form.quantity.data,
            unit=form.unit.data,
            price_per_unit=form.price_per_unit.data,
            quality=form.quality.data,
            description=form.description.data,
            status="active",
        )

        db.session.add(crop)
        db.session.commit()

        flash("Crop listing added successfully.", "success")
        return redirect(url_for("my_crops"))

    return render_template(
        "add_crop.html",
        form=form,
        title="Add Crop",
    )


@app.route("/crops/<int:crop_id>/edit", methods=["GET", "POST"])
@role_required("farmer")
def edit_crop(crop_id):
    crop = db.get_or_404(Crop, crop_id)

    if crop.farmer_id != current_user.id:
        abort(403)

    if crop.status == "sold":
        flash("Sold crops cannot be edited.", "warning")
        return redirect(url_for("my_crops"))

    form = CropForm(obj=crop)

    if form.validate_on_submit():
        crop.name = form.name.data.strip()
        crop.quantity = form.quantity.data
        crop.unit = form.unit.data
        crop.price_per_unit = form.price_per_unit.data
        crop.quality = form.quality.data
        crop.description = form.description.data

        if crop.status == "hidden":
            crop.status = "active"

        db.session.commit()

        flash("Crop listing updated successfully.", "success")
        return redirect(url_for("my_crops"))

    return render_template(
        "add_crop.html",
        form=form,
        title="Edit Crop",
    )


@app.route("/crops/<int:crop_id>/delete", methods=["POST"])
@role_required("farmer")
def delete_crop(crop_id):
    crop = db.get_or_404(Crop, crop_id)

    if crop.farmer_id != current_user.id:
        abort(403)

    if crop.orders or crop.negotiations:
        crop.status = "hidden"
        flash(
            "Crop hidden because it has order or negotiation history.",
            "info",
        )
    else:
        db.session.delete(crop)
        flash("Crop deleted successfully.", "success")

    db.session.commit()
    return redirect(url_for("my_crops"))


@app.route("/my-crops")
@role_required("farmer")
def my_crops():
    crops = Crop.query.filter_by(
        farmer_id=current_user.id
    ).order_by(
        Crop.created_at.desc()
    ).all()

    return render_template("my_crops.html", crops=crops)


# -------------------- ORDERS --------------------

@app.route("/crops/<int:crop_id>/order", methods=["POST"])
@role_required("buyer")
def place_order(crop_id):
    crop = db.get_or_404(Crop, crop_id)
    form = OrderForm()

    if not form.validate_on_submit():
        flash("Please enter a valid quantity.", "danger")
        return redirect(url_for("crop_detail", crop_id=crop_id))

    quantity = form.quantity.data

    if crop.status != "active":
        flash("This crop is not available.", "warning")
    elif crop.farmer_id == current_user.id:
        flash("You cannot order your own crop.", "warning")
    elif quantity > crop.quantity:
        flash(
            "Requested quantity is greater than the available stock.",
            "danger",
        )
    else:
        order = Order(
            crop_id=crop.id,
            buyer_id=current_user.id,
            farmer_id=crop.farmer_id,
            quantity=quantity,
            price_per_unit=crop.price_per_unit,
            total_amount=round(
                quantity * crop.price_per_unit,
                2,
            ),
            status="pending",
        )

        db.session.add(order)
        db.session.commit()

        flash("Order request sent to the farmer.", "success")
        return redirect(url_for("my_orders"))

    return redirect(url_for("crop_detail", crop_id=crop_id))


@app.route("/my-orders")
@role_required("buyer")
def my_orders():
    orders = Order.query.filter_by(
        buyer_id=current_user.id
    ).order_by(
        Order.created_at.desc()
    ).all()

    return render_template("my_orders.html", orders=orders)


# -------------------- BUYER-SELLER NEGOTIATIONS --------------------

@app.route("/negotiations")
@role_required("buyer", "farmer")
def negotiations():
    if current_user.role == "buyer":
        conversations = Negotiation.query.filter_by(
            buyer_id=current_user.id
        ).order_by(Negotiation.updated_at.desc()).all()
    else:
        conversations = Negotiation.query.filter_by(
            farmer_id=current_user.id
        ).order_by(Negotiation.updated_at.desc()).all()

    return render_template(
        "negotiations.html",
        negotiations=conversations,
        reply_form=NegotiationReplyForm(),
    )


@app.route("/negotiations/new/<int:crop_id>", methods=["POST"])
@role_required("buyer")
def start_negotiation(crop_id):
    crop = db.get_or_404(Crop, crop_id)
    form = NegotiationOfferForm()

    if not form.validate_on_submit():
        flash("Enter a valid quantity and offer price.", "danger")
        return redirect(url_for("crop_detail", crop_id=crop.id))

    if crop.status != "active" or crop.quantity <= 0:
        flash("This crop is currently unavailable for negotiation.", "warning")
        return redirect(url_for("crop_detail", crop_id=crop.id))

    if crop.farmer_id == current_user.id:
        abort(403)

    if form.quantity.data > crop.quantity:
        flash("Your offer quantity is greater than the available stock.", "danger")
        return redirect(url_for("crop_detail", crop_id=crop.id))

    existing = Negotiation.query.filter_by(
        crop_id=crop.id,
        buyer_id=current_user.id,
        status="open",
    ).first()
    if existing:
        flash("You already have an open negotiation for this crop.", "info")
        return redirect(url_for("negotiations"))

    negotiation = Negotiation(
        crop_id=crop.id,
        buyer_id=current_user.id,
        farmer_id=crop.farmer_id,
        quantity=form.quantity.data,
        status="open",
    )
    db.session.add(negotiation)
    db.session.flush()
    db.session.add(NegotiationMessage(
        negotiation_id=negotiation.id,
        sender_id=current_user.id,
        offer_price=form.offer_price.data,
        message=(form.message.data or "").strip(),
    ))
    db.session.commit()

    flash("Your offer has been sent to the farmer.", "success")
    return redirect(url_for("negotiations"))


@app.route("/negotiations/<int:negotiation_id>/reply", methods=["POST"])
@role_required("buyer", "farmer")
def reply_to_negotiation(negotiation_id):
    negotiation = db.get_or_404(Negotiation, negotiation_id)
    is_party = current_user.id in (negotiation.buyer_id, negotiation.farmer_id)
    if not is_party:
        abort(403)

    if negotiation.status != "open":
        flash("This negotiation is already closed.", "warning")
        return redirect(url_for("negotiations"))

    if negotiation.messages[-1].sender_id == current_user.id:
        flash("Wait for the other party to respond before sending another offer.", "warning")
        return redirect(url_for("negotiations"))

    form = NegotiationReplyForm()
    if not form.validate_on_submit():
        flash("Enter a valid counter-offer price.", "danger")
        return redirect(url_for("negotiations"))

    if (
        negotiation.crop.status != "active"
        or negotiation.quantity > negotiation.crop.quantity
    ):
        flash("The requested quantity is no longer available.", "danger")
        return redirect(url_for("negotiations"))

    db.session.add(NegotiationMessage(
        negotiation_id=negotiation.id,
        sender_id=current_user.id,
        offer_price=form.offer_price.data,
        message=(form.message.data or "").strip(),
    ))
    negotiation.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Your counter-offer has been sent.", "success")
    return redirect(url_for("negotiations"))


@app.route(
    "/negotiations/<int:negotiation_id>/<action>",
    methods=["POST"],
)
@role_required("buyer", "farmer")
def decide_negotiation(negotiation_id, action):
    if action not in ("accept", "reject"):
        abort(400)

    negotiation = db.get_or_404(Negotiation, negotiation_id)
    if current_user.id not in (negotiation.buyer_id, negotiation.farmer_id):
        abort(403)

    if negotiation.status != "open":
        flash("This negotiation has already been processed.", "warning")
        return redirect(url_for("negotiations"))

    if negotiation.messages[-1].sender_id == current_user.id:
        flash("Only the recipient of the latest offer can respond to it.", "warning")
        return redirect(url_for("negotiations"))

    if action == "reject":
        negotiation.status = "rejected"
        db.session.commit()
        flash("Negotiation declined.", "info")
        return redirect(url_for("negotiations"))

    crop = negotiation.crop
    if crop.status != "active" or negotiation.quantity > crop.quantity:
        flash("The requested quantity is no longer available.", "danger")
        return redirect(url_for("negotiations"))

    agreed_price = negotiation.messages[-1].offer_price
    order = Order(
        crop_id=crop.id,
        buyer_id=negotiation.buyer_id,
        farmer_id=negotiation.farmer_id,
        quantity=negotiation.quantity,
        price_per_unit=agreed_price,
        total_amount=round(negotiation.quantity * agreed_price, 2),
        status="accepted",
    )
    crop.quantity = round(crop.quantity - negotiation.quantity, 3)
    if crop.quantity <= 0:
        crop.quantity = 0
        crop.status = "sold"

    db.session.add(order)
    negotiation.status = "accepted"
    negotiation.agreed_price = agreed_price
    db.session.flush()
    negotiation.order_id = order.id
    db.session.commit()

    flash("Offer accepted. The agreed order has been confirmed.", "success")
    return redirect(url_for("negotiations"))


@app.route("/manage-orders")
@role_required("farmer")
def manage_orders():
    orders = Order.query.filter_by(
        farmer_id=current_user.id
    ).order_by(
        Order.created_at.desc()
    ).all()

    return render_template("manage_orders.html", orders=orders)


@app.route("/orders/<int:order_id>/<action>", methods=["POST"])
@role_required("farmer")
def update_order(order_id, action):
    order = db.get_or_404(Order, order_id)

    if order.farmer_id != current_user.id:
        abort(403)

    if order.status != "pending":
        flash("This order has already been processed.", "warning")
        return redirect(url_for("manage_orders"))

    if action == "accept":
        if (
            order.crop.status != "active"
            or order.quantity > order.crop.quantity
        ):
            flash("Not enough crop stock is available.", "danger")
            return redirect(url_for("manage_orders"))

        order.crop.quantity = round(
            order.crop.quantity - order.quantity,
            3,
        )

        if order.crop.quantity <= 0:
            order.crop.quantity = 0
            order.crop.status = "sold"

        order.status = "accepted"
        flash("Order accepted.", "success")

    elif action == "reject":
        order.status = "rejected"
        flash("Order rejected.", "info")

    else:
        abort(400)

    db.session.commit()
    return redirect(url_for("manage_orders"))


# -------------------- GOVERNMENT SCHEMES --------------------

@app.route("/schemes")
def schemes():
    items = Scheme.query.filter_by(
        is_active=True
    ).order_by(
        Scheme.created_at.desc()
    ).all()

    return render_template("schemes.html", schemes=items)


@app.route("/schemes/<int:scheme_id>")
def scheme_detail(scheme_id):
    scheme = db.get_or_404(Scheme, scheme_id)

    if not scheme.is_active:
        if (
            not current_user.is_authenticated
            or current_user.role != "admin"
        ):
            abort(404)

    return render_template("scheme_detail.html", scheme=scheme)


@app.route("/admin/schemes/add", methods=["GET", "POST"])
@role_required("admin")
def add_scheme():
    form = SchemeForm()

    if form.validate_on_submit():
        scheme = Scheme(
            name=form.name.data.strip(),
            description=form.description.data.strip(),
            eligibility=form.eligibility.data,
            documents=form.documents.data,
            application_steps=form.application_steps.data,
            official_url=form.official_url.data,
            is_active=True,
        )

        db.session.add(scheme)
        db.session.commit()

        flash("Scheme added successfully.", "success")
        return redirect(url_for("schemes"))

    return render_template(
        "scheme_detail.html",
        scheme=None,
        form=form,
    )


# -------------------- FARMER ARTICLES --------------------

@app.route("/articles")
def articles():
    items = Article.query.order_by(
        Article.created_at.desc()
    ).all()

    return render_template("articles.html", articles=items)


@app.route("/admin/articles/add", methods=["GET", "POST"])
@app.route("/articles/add", methods=["GET", "POST"])
@role_required("admin", "farmer")
def add_article():
    form = ArticleForm()

    if form.validate_on_submit():
        article = Article(
            title=form.title.data.strip(),
            category=form.category.data,
            content=form.content.data,
            language=form.language.data,
            author_id=current_user.id,
        )

        db.session.add(article)
        db.session.commit()

        flash("Article published successfully.", "success")
        return redirect(url_for("articles"))

    return render_template(
        "articles.html",
        articles=[],
        form=form,
    )


# -------------------- CROP HEALTH ADVISORY --------------------

@app.route("/disease-detector", methods=["GET", "POST"])
@role_required("farmer")
def disease_detector():
    result = None
    error = None
    selected_crop = ""
    selected_symptom = ""

    if request.method == "POST":
        selected_crop = request.form.get("crop_type", "")
        selected_symptom = request.form.get("symptom", "")
        upload = request.files.get("crop_image")

        if selected_crop not in CROPS or selected_symptom not in SYMPTOMS:
            error = "Please select a supported crop and the closest visible symptom."
        elif not upload or not upload.filename:
            error = "Please choose a crop photo to continue."
        else:
            image_bytes = upload.stream.read(MAX_DISEASE_IMAGE_BYTES + 1)
            if len(image_bytes) > MAX_DISEASE_IMAGE_BYTES:
                error = "The photo must be 5 MB or smaller."
            else:
                try:
                    with Image.open(io.BytesIO(image_bytes)) as image:
                        if image.format not in {"JPEG", "PNG", "WEBP"}:
                            error = "Please upload a JPG, PNG, or WEBP photo."
                        elif image.width * image.height > 20_000_000:
                            error = "The photo dimensions are too large. Please use a smaller image."
                        else:
                            image.verify()
                except (Image.DecompressionBombError, UnidentifiedImageError, OSError):
                    error = "That file is not a valid JPG, PNG, or WEBP photo."

            if not error:
                result = get_advisory(selected_crop, selected_symptom)

    return render_template(
        "disease_detector.html",
        crops=CROPS,
        symptoms=SYMPTOMS,
        selected_crop=selected_crop,
        selected_symptom=selected_symptom,
        result=result,
        error=error,
    )


# -------------------- HELP AND SUPPORT --------------------

@app.route("/help-requests", methods=["GET", "POST"])
@login_required
def help_requests():
    form = HelpRequestForm()

    if form.validate_on_submit():
        item = HelpRequest(
            user_id=current_user.id,
            subject=form.subject.data.strip(),
            category=form.category.data,
            description=form.description.data.strip(),
        )

        db.session.add(item)
        db.session.commit()

        flash("Your help request has been submitted.", "success")
        return redirect(url_for("help_requests"))

    if current_user.role == "admin":
        requests_list = HelpRequest.query.order_by(
            HelpRequest.created_at.desc()
        ).all()
    else:
        requests_list = HelpRequest.query.filter_by(
            user_id=current_user.id
        ).order_by(
            HelpRequest.created_at.desc()
        ).all()

    return render_template(
        "help_requests.html",
        form=form,
        requests=requests_list,
        response_form=AdminResponseForm(),
    )


@app.route(
    "/admin/help-requests/<int:request_id>/update",
    methods=["POST"],
)
@role_required("admin")
def update_help_request(request_id):
    item = db.get_or_404(HelpRequest, request_id)
    form = AdminResponseForm()

    if form.validate_on_submit():
        item.status = form.status.data
        item.admin_response = form.admin_response.data

        db.session.commit()
        flash("Help request updated successfully.", "success")
    else:
        flash("Please check the help request form.", "danger")

    return redirect(url_for("help_requests"))


# -------------------- ADMIN MANAGEMENT --------------------

@app.route("/admin/users")
@role_required("admin")
def admin_users():
    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return render_template("admin_users.html", users=users)


@app.route("/admin/crops")
@role_required("admin")
def admin_crops():
    crops = Crop.query.order_by(
        Crop.created_at.desc()
    ).all()

    return render_template("admin_crops.html", crops=crops)


@app.route("/admin/crops/<int:crop_id>/toggle", methods=["POST"])
@role_required("admin")
def admin_toggle_crop(crop_id):
    crop = db.get_or_404(Crop, crop_id)

    if crop.status == "sold":
        flash("Sold crops cannot be reactivated.", "warning")
    elif crop.status == "active":
        crop.status = "hidden"
        flash("Crop listing hidden successfully.", "success")
    else:
        crop.status = "active"
        flash("Crop listing activated successfully.", "success")

    db.session.commit()
    return redirect(url_for("admin_crops"))



# -------------------- HELP DESK CHATBOT --------------------

@app.route("/api/chatbot", methods=["POST"])
@csrf.exempt
def chatbot():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return {
            "response": "नमस्ते! कृपया अपना प्रश्न लिखें। मैं आपकी सहायता के लिए तैयार हूँ। 🙏",
            "suggestions": ["🏛️ सरकारी योजनाएं", "🌾 फसल कैसे बेचें?", "🛒 उपलब्ध फसलें", "💬 हेल्प सपोर्ट"],
        }

    msg = message.lower()

    # 1. Greetings
    if any(k in msg for k in ["namaste", "namaskar", "hello", "hi", "hey", "नमस्ते", "नमस्कार", "राम राम", "प्रणाम", "kaise ho", "kisanmitra"]):
        return {
            "response": "🙏 <strong>नमस्ते किसान भाई/बहन!</strong><br><br>"
                        "मैं किसान सेतु का <strong>'किसान सहायक' (Helpdesk Bot)</strong> हूँ।<br>"
                        "मैं आपकी सरकारी योजनाओं, फसल खरीद-बिक्री, जैविक खेती, या किसी भी समस्या में तत्काल सहायता कर सकता हूँ।<br><br>"
                        "नीचे दिए गए किसी विकल्प पर क्लिक करें या अपना सवाल लिखकर पूछें:",
            "suggestions": ["🏛️ सरकारी योजनाएं", "🌾 फसल कैसे बेचें?", "🛒 उपलब्ध फसलें", "🌿 जैविक खाद व कीटनाशक", "💬 हेल्प सपोर्ट टिकट"],
        }

    # 2. PM-KISAN / किसान सम्मान निधि
    elif any(k in msg for k in ["pm kisan", "pm-kisan", "pmkisan", "सम्मान निधि", "samman nidhi", "6000", "2000", "installment", "किस्त"]):
        return {
            "response": "🌾 <strong>प्रधानमंत्री किसान सम्मान निधि योजना (PM-KISAN):</strong><br><br>"
                        "• <strong>लाभ:</strong> पात्र किसानों को प्रतिवर्ष <strong>₹6,000</strong> की वित्तीय सहायता ₹2,000 की 3 किस्तों में सीधे बैंक खाते में (DBT) दी जाती है।<br>"
                        "• <strong>पात्रता:</strong> भारत के सभी छोटे एवं सीमांत भूमिधारक किसान परिवार जिनके नाम कृषि भूमि का स्वामित्व है।<br>"
                        "• <strong>आवश्यक दस्तावेज:</strong> आधार कार्ड, बैंक पासबुक (Aadhaar Seeded), खतौनी (भूलेख नकल), मोबाइल नंबर।<br>"
                        "• <strong>आवेदन कैसे करें:</strong> आधिकारिक पोर्टल <a href='https://pmkisan.gov.in' target='_blank' class='text-success fw-bold'>pmkisan.gov.in</a> पर 'New Farmer Registration' से या नजदीकी CSC केंद्र से आवेदन करें।<br><br>"
                        "💡 किसान सेतु पर सभी योजनाएं देखने के लिए <a href='/schemes' class='text-success fw-bold'>योजनाएं पेज</a> देखें।",
            "suggestions": ["🛡️ फसल बीमा योजना (PMFBY)", "💳 किसान क्रेडिट कार्ड (KCC)", "🌾 फसल कैसे बेचें?", "🏛️ अन्य योजनाएं"],
        }

    # 3. Fasal Bima / बीमा
    elif any(k in msg for k in ["bima", "fasal bima", "pmfby", "बीमा", "फसल बीमा", "मुआवजा", "नुकसान", "claim"]):
        return {
            "response": "🛡️ <strong>प्रधानमंत्री फसल बीमा योजना (PMFBY):</strong><br><br>"
                        "• <strong>सुरक्षा:</strong> सूखा, बाढ़, ओलावृष्टि, कीट या बेमौसम बारिश से फसल नष्ट होने पर शत-प्रतिशत मुआवजा सुरक्षा।<br>"
                        "• <strong>प्रीमियम दरें:</strong><br>"
                        "  - खरीफ फसल: मात्र <strong>2%</strong><br>"
                        "  - रबी फसल: मात्र <strong>1.5%</strong><br>"
                        "  - बागवानी व व्यावसायिक फसलें: <strong>5%</strong><br>"
                        "• <strong>दावा (Claim) प्रक्रिया:</strong> फसल नुकसान होने के <strong>72 घंटे के भीतर</strong> बीमा कंपनी या टोल-फ्री नंबर <strong>14447</strong> पर सूचना दर्ज कराएं।<br>"
                        "• आधिकारिक वेबसाइट: <a href='https://pmfby.gov.in' target='_blank' class='text-success fw-bold'>pmfby.gov.in</a>",
            "suggestions": ["💳 KCC लोन योजना", "🌾 PM-KISAN योजना", "🌿 जैविक खाद व कीटनाशक", "💬 कस्टमर सपोर्ट"],
        }

    # 4. KCC / लोन / ऋण
    elif any(k in msg for k in ["kcc", "loan", "credit card", "लोन", "ऋण", "कर्ज", "क्रेडिट कार्ड", "ब्याज"]):
        return {
            "response": "💳 <strong>किसान क्रेडिट कार्ड (KCC) योजना:</strong><br><br>"
                        "• <strong>ब्याज दर:</strong> समय पर भुगतान करने पर ब्याज दर मात्र <strong>4% प्रतिवर्ष</strong> (3% सरकारी सबवेंशन के बाद) रहती है।<br>"
                        "• <strong>बिना गारंटी ऋण:</strong> ₹1.60 लाख तक का ऋण बिना किसी बंधक (Collateral-free) के दिया जाता है।<br>"
                        "• <strong>उपयोग:</strong> खाद, बीज, कीटनाशक, डीजल और कृषि मशीनरी रखरखाव के लिए।<br>"
                        "• <strong>आवेदन:</strong> नजदीकी बैंक शाखा (SBI, PNB, ग्रामीण बैंक) में आधार कार्ड, 2 फोटो और खतौनी लेकर KCC फॉर्म भरें।",
            "suggestions": ["🏛️ अन्य सरकारी योजनाएं", "🌾 फसल कैसे बेचें?", "🛒 फसल कैसे खरीदें?", "💬 हेल्प सपोर्ट"],
        }

    # 5. Sell Crop / फसल कैसे बेचें
    elif any(k in msg for k in ["bech", "sell", "listing", "बेच", "बिक्री", "add crop", "फसल कैसे बेचें", "sell crop"]):
        return {
            "response": "🌱 <strong>किसान सेतु पर अपनी फसल कैसे बेचें?</strong><br><br>"
                        "1. अपने किसान अकाउंट से लॉगिन करें।<br>"
                        "2. ऊपर मेन्यू या डैशबोर्ड पर <strong><a href='/crops/add' class='text-success fw-bold'>'+ Sell Your Crops'</a></strong> पर क्लिक करें।<br>"
                        "3. अपनी फसल का नाम (उदा. गेहूं, धान, टमाटर), कुल मात्रा, यूनिट (kg/क्विंटल) और प्रति यूनिट भाव (₹) दर्ज करें।<br>"
                        "4. 'Save Crop' पर क्लिक करते ही आपकी फसल मार्केटप्लेस में लाइव हो जाएगी।<br>"
                        "5. खरीदार (Buyers) सीधे आपसे ऑर्डर करेंगे, जिसे आप <a href='/manage-orders' class='text-success fw-bold'>'Orders'</a> पेज पर Accept कर सकते हैं।",
            "suggestions": ["🛒 उपलब्ध फसलें देखें", "📦 ऑर्डर्स कैसे देखें?", "🏛️ सरकारी योजनाएं", "💬 सहायता केंद्र"],
        }

    # 6. Buy Crop / ऑर्डर कैसे करें
    elif any(k in msg for k in ["buy", "order", "kharid", "खरीद", "ऑर्डर", "order kaise", "purchase"]):
        return {
            "response": "🛒 <strong>फसल कैसे खरीदें (How to Order)?</strong><br><br>"
                        "1. ऊपर मेन्यू में <strong><a href='/crops' class='text-success fw-bold'>'Browse Crops'</a></strong> पर जाएं।<br>"
                        "2. अपनी पसंद की फसल पर 'View Details' बटन दबाएं।<br>"
                        "3. जितनी मात्रा चाहिए दर्ज करें (कुल मूल्य अपने आप कैलकुलेट हो जाएगा)।<br>"
                        "4. 'Place Order' पर क्लिक करें। किसान को आपका ऑर्डर मिल जाएगा और वे आपसे संपर्क करेंगे।<br>"
                        "5. आप <a href='/my-orders' class='text-success fw-bold'>'My Orders'</a> पेज पर अपने ऑर्डर की स्थिति ट्रैक कर सकते हैं।",
            "suggestions": ["🛒 उपलब्ध फसलें", "🌾 फसल कैसे बेचें?", "📦 मेरे ऑर्डर्स", "💬 हेल्प डेस्क"],
        }

    # 7. Check Available Crops (Live DB Query)
    elif any(k in msg for k in ["available", "crops", "list", "उपलब्ध", "फसलें", "मार्केट", "कीमत", "भाव", "price"]):
        active_crops = Crop.query.filter_by(status="active").limit(5).all()
        if active_crops:
            crop_lines = [f"• <strong>{c.name}</strong> — ₹{c.price_per_unit:.2f}/{c.unit} (उपलब्ध: {c.quantity} {c.unit})" for c in active_crops]
            response_text = "🌾 <strong>वर्तमान में किसान सेतु पर उपलब्ध प्रमुख फसलें:</strong><br><br>" + "<br>".join(crop_lines) + "<br><br>👉 सभी फसलें देखने और ऑर्डर करने के लिए <a href='/crops' class='text-success fw-bold'>Browse Crops</a> पर जाएं।"
        else:
            response_text = "🌾 अभी मार्केटप्लेस में फसलें अपडेट हो रही हैं। आप <a href='/crops' class='text-success fw-bold'>Browse Crops</a> पेज पर जाकर देख सकते हैं।"
        return {
            "response": response_text,
            "suggestions": ["🛒 फसल कैसे खरीदें?", "🌾 फसल कैसे बेचें?", "🏛️ सरकारी योजनाएं"],
        }

    # 8. Check Active Schemes (Live DB Query)
    elif any(k in msg for k in ["scheme", "yojana", "योजना", "सब्सिडी", "subsidy", "सरकारी योजना", "योजनाएं"]):
        schemes = Scheme.query.filter_by(is_active=True).limit(6).all()
        if schemes:
            scheme_lines = [f"• <a href='/schemes/{s.id}' class='text-success fw-bold'>{s.name}</a>" for s in schemes]
            response_text = "🏛️ <strong>किसान सेतु पर उपलब्ध मुख्य सरकारी योजनाएं:</strong><br><br>" + "<br>".join(scheme_lines) + "<br><br>👉 पूरी पात्रता और आवेदन विधि के लिए <a href='/schemes' class='text-success fw-bold'>Govt. Schemes पेज</a> देखें।"
        else:
            response_text = "🏛️ सरकारी योजनाओं की जानकारी के लिए <a href='/schemes' class='text-success fw-bold'>योजनाएं पेज</a> देखें।"
        return {
            "response": response_text,
            "suggestions": ["🌾 PM-KISAN योजना", "🛡️ फसल बीमा योजना", "💳 KCC ऋण", "🌱 ड्रिप सिंचाई सब्सिडी"],
        }

    # 9. Organic Farming / Fertilizers / Pesticides
    elif any(k in msg for k in ["organic", "jaivik", "khad", "fertilizer", "pest", "जैविक", "खाद", "कीटनाशक", "नीमास्त्र", "केंचुआ", "vermicompost", "chepa", "माहू"]):
        return {
            "response": "🌿 <strong>जैविक खाद व प्राकृतिक कीटनाशक समाधान:</strong><br><br>"
                        "• <strong>नीमास्त्र (रस चूसक कीटों व माहू के लिए):</strong> 5 किग्रा नीम पत्ते + 5 लीटर गोमूत्र + 2 किग्रा गाय का गोबर 100 लीटर पानी में 48 घंटे सड़ाकर कपड़े से छानकर छिड़कें।<br>"
                        "• <strong>वर्मीकम्पोस्ट (केंचुआ खाद):</strong> गोबर व फसल अवशेषों से 45-60 दिनों में चाय पत्ती जैसी जैविक खाद तैयार होती है जो पैदावार 25% तक बढ़ाती है।<br><br>"
                        "📖 पूरी विधि विस्तार से पढ़ने के लिए हमारे <strong><a href='/articles' class='text-success fw-bold'>Farming Guides (कृषि लेख)</a></strong> देखें।",
            "suggestions": ["📖 कृषि लेख पढ़ें", "🏛️ सरकारी योजनाएं", "🌾 फसल कैसे बेचें?"],
        }

    # 10. Soil Health / मृदा स्वास्थ्य कार्ड
    elif any(k in msg for k in ["soil", "mitti", "मिट्टी", "मृदा", "soil health"]):
        return {
            "response": "🧪 <strong>मृदा स्वास्थ्य कार्ड योजना (Soil Health Card):</strong><br><br>"
                        "• आपके खेत की मिट्टी में 12 पोषक तत्वों (नाइट्रोजन, फास्फोरस, पोटाश, जिंक आदि) की निःशुल्क जांच होती है।<br>"
                        "• सही मात्रा में संतुलित खाद डालने से खाद की 30% बचत होती है और फसल पैदावार बढ़ती है।<br>"
                        "• अपने नजदीकी कृषि विज्ञान केंद्र (KVK) या किसान मित्र से संपर्क करके मिट्टी का नमूना जमा करें।",
            "suggestions": ["🌿 जैविक खाद व कीटनाशक", "🌾 PM-KISAN योजना", "🏛️ अन्य योजनाएं"],
        }

    # 11. Help desk / Contact Support / Human assistance
    elif any(k in msg for k in ["help", "support", "contact", "shikayat", "problem", "सहायता", "मदद", "शिकायत", "सपोर्ट", "कॉल", "ticket"]):
        return {
            "response": "🤝 <strong>किसान सेतु सहायता केंद्र (Help Desk):</strong><br><br>"
                        "यदि आपकी कोई विशिष्ट समस्या, खाता संबंधी सवाल या सुझाव है, तो आप हमारी सहायता टीम को सीधे टिकट भेज सकते हैं:<br><br>"
                        "👉 <strong><a href='/help-requests' class='text-success fw-bold'>यहाँ क्लिक करके Help Request सबमिट करें</a></strong><br><br>"
                        "हमारी सपोर्ट टीम 24-48 घंटों के भीतर आपके अनुरोध का समाधान करेगी।",
            "suggestions": ["🏛️ सरकारी योजनाएं", "🌾 फसल कैसे बेचें?", "🛒 उपलब्ध फसलें"],
        }

    # 12. Thank you / धन्यवाद
    elif any(k in msg for k in ["dhanyawad", "shukriya", "thanks", "thank you", "धन्यवाद", "शुक्रिया", "great", "achha"]):
        return {
            "response": "🌾 <strong>आपका बहुत-बहुत धन्यवाद!</strong><br><br>किसान सेतु सदैव हमारे अन्नदाताओं और खरीदारों की सेवा में समर्पित है। यदि कोई और सहायता चाहिए हो तो बेझिझक पूछें! जय जवान, जय किसान! 🌱",
            "suggestions": ["🏛️ सरकारी योजनाएं", "🌾 फसल मार्केटप्लेस", "📖 कृषि लेख"],
        }

    # 13. Default Fallback
    else:
        return {
            "response": f"नमस्ते! आपने पूछा: <em>'{message}'</em><br><br>"
                        "मैं आपकी बेहतर सहायता के लिए निम्नलिखित विषयों में जानकारी दे सकता हूँ:<br>"
                        "• <strong>सरकारी योजनाएं:</strong> PM-KISAN, फसल बीमा, KCC ऋण, सिंचाई सब्सिडी<br>"
                        "• <strong>मार्केटप्लेस:</strong> फसल बेचना, खरीदना और वर्तमान भाव<br>"
                        "• <strong>जैविक खेती:</strong> प्राकृतिक खाद और कीटनाशक बनाने की विधि<br>"
                        "• <strong>हेल्प सपोर्ट:</strong> समस्या समाधान के लिए <a href='/help-requests' class='text-success fw-bold'>Help Request</a> सबमिट करें।",
            "suggestions": ["🏛️ सरकारी योजनाएं", "🌾 फसल कैसे बेचें?", "🛒 उपलब्ध फसलें", "💬 हेल्प सपोर्ट टिकट"],
        }


# -------------------- ERROR HANDLERS --------------------

@app.errorhandler(403)
def forbidden(error):
    return render_template(
        "404.html",
        message="You do not have permission to access this page.",
    ), 403


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "404.html",
        message="The page you are looking for was not found.",
    ), 404




def seed_initial_data():

    if Scheme.query.count() == 0:

        schemes = [

            Scheme(

                name="प्रधानमंत्री किसान सम्मान निधि योजना (PM-KISAN)",

                description="देश के सभी भूमिधारक किसान परिवारों को वित्तीय सहायता प्रदान करने के उद्देश्य से शुरू की गई केंद्रीय योजना। इसके तहत पात्र किसानों को प्रतिवर्ष ₹6,000 की वित्तीय सहायता तीन समान किस्तों (₹2,000 प्रत्येक) में सीधे बैंक खाते में (DBT) दी जाती है।",

                eligibility="भारत के सभी छोटे और सीमांत भूमिधारक किसान परिवार जिनके नाम कृषि भूमि का वैध स्वामित्व है।",

                documents="आधार कार्ड, बैंक पासबुक (Aadhaar linked/NPCI), खतौनी/भूलेख की नकल, मोबाइल नंबर।",

                application_steps="1. आधिकारिक वेबसाइट pmkisan.gov.in पर जाएं।\n2. 'Farmers Corner' में जाकर 'New Farmer Registration' चुनें।\n3. आधार नंबर व राज्य दर्ज कर सबमिट करें या नजदीकी CSC केंद्र पर जाएं।",

                official_url="https://pmkisan.gov.in",

                is_active=True,

            ),

            Scheme(

                name="प्रधानमंत्री फसल बीमा योजना (PMFBY)",

                description="अप्रत्याशित प्राकृतिक आपदाओं (सूखा, बाढ़, ओलावृष्टि) तथा कीटों एवं रोगों से फसल नुकसान पर किसानों को व्यापक बीमा सुरक्षा और क्षतिपूर्ति दी जाती है। खरीफ फसलों के लिए मात्र 2% और रबी फसलों के लिए 1.5% प्रीमियम देना होता है।",

                eligibility="सभी किसान (बटाईदार और काश्तकार सहित) जो अधिसूचित क्षेत्रों में अधिसूचित फसलें उगा रहे हैं।",

                documents="आधार कार्ड, जमीन का पर्चा/खतौनी, बुवाई प्रमाण पत्र (पटवारी/कृषि पर्यवेक्षक द्वारा), बैंक खाता पासबुक।",

                application_steps="1. pmfby.gov.in पर किसान अनुभाग में रजिस्टर करें।\n2. फसल व बैंक खाता विवरण दर्ज करें।\n3. नजदीकी बैंक शाखा या जन सेवा केंद्र (CSC) से भी बीमा कराएं।",

                official_url="https://pmfby.gov.in",

                is_active=True,

            ),

            Scheme(

                name="किसान क्रेडिट कार्ड योजना (Kisan Credit Card - KCC)",

                description="किसानों को खाद, बीज, कीटनाशक और कृषि उपकरणों के लिए रियायती ब्याज दर (समय पर भुगतान पर मात्र 4%) पर अल्पावधि ऋण उपलब्ध कराया जाता है। इसमें ₹1.60 लाख तक का ऋण बिना किसी गिरवी (Collateral-free) के मिलता है।",

                eligibility="सभी किसान, काश्तकार, स्वयं सहायता समूह (SHG), पशुपालक एवं मत्स्यपालक।",

                documents="आवेदन पत्र, 2 पासपोर्ट फोटो, आधार कार्ड/वोटर आईडी, जमीन की खतौनी एवं फसल बुवाई का विवरण।",

                application_steps="1. नजदीकी बैंक शाखा (SBI, PNB, ग्रामीण बैंक) में KCC फॉर्म भरें।\n2. राजस्व दस्तावेज संलग्न करें। सत्यापन के बाद 14 दिनों में कार्ड जारी होता है।",

                official_url="https://agricoop.nic.in",

                is_active=True,

            ),

            Scheme(

                name="मृदा स्वास्थ्य कार्ड योजना (Soil Health Card Scheme)",

                description="किसानों को उनके खेत की मिट्टी की गुणवत्ता, पोषक तत्वों की स्थिति (12 मुख्य पैरामीटर) और संतुलित उर्वरक प्रयोग की विस्तृत रिपोर्ट दी जाती है जिससे उत्पादन 20-30% बढ़ता है और खाद की लागत घटती है।",

                eligibility="देश के सभी किसान अपनी किसी भी कृषि भूमि का मृदा परीक्षण निःशुल्क करा सकते हैं।",

                documents="आधार कार्ड, खेत का खसरा नंबर, मोबाइल नंबर।",

                application_steps="1. स्थानीय कृषि पर्यवेक्षक या किसान मित्र से संपर्क करें।\n2. खेत से मिट्टी का नमूना लेकर कृषि विज्ञान केंद्र (KVK) में जमा करें।\n3. रिपोर्ट कार्ड ऑनलाइन soilhealth.dac.gov.in से डाउनलोड करें।",

                official_url="https://soilhealth.dac.gov.in",

                is_active=True,

            ),

            Scheme(

                name="प्रधानमंत्री कृषि सिंचाई योजना (PMKSY) - 'प्रति बूंद अधिक फसल'",

                description="खेतों तक सिंचाई सुविधा पहुंचाने और सूक्ष्म सिंचाई (ड्रिप व स्प्रिंकलर) तकनीकों पर 45% से 55% तक की सरकारी सब्सिडी दी जाती है। इससे 40-50% पानी की बचत होती है और उपज में उल्लेखनीय वृद्धि होती है।",

                eligibility="सभी किसान जिनके पास कृषि योग्य भूमि और सुनिश्चित जल स्रोत (बोरवेल/कुआं/तालाब) है।",

                documents="आधार कार्ड, भूमि का स्वामित्व प्रमाण, जल स्रोत का प्रमाण, बैंक पासबुक।",

                application_steps="1. राज्य के उद्यान/कृषि विभाग के ऑनलाइन पोर्टल पर आवेदन करें।\n2. तकनीकी टीम के सर्वे के बाद उपकरण स्थापित होते हैं और सब्सिडी खाते में आती है।",

                official_url="https://pmksy.gov.in",

                is_active=True,

            ),

            Scheme(

                name="परम्परागत कृषि विकास योजना (PKVY) - जैविक खेती प्रोत्साहन",

                description="जैविक खेती को बढ़ावा देने के लिए किसानों के समूह (क्लस्टर) बनाकर प्रति हेक्टेयर ₹50,000 की वित्तीय सहायता दी जाती है, जिसमें जैविक खाद, जैविक कीटनाशक और प्रमाणीकरण शामिल है।",

                eligibility="20 या अधिक किसानों का समूह जो न्यूनतम 50 एकड़ में सामूहिक जैविक खेती करना चाहते हों।",

                documents="किसान समूह का विवरण, आधार कार्ड, भूमि दस्तावेज, बैंक खाता।",

                application_steps="स्थानीय जिला कृषि अधिकारी / आत्मा (ATMA) परियोजना निदेशक कार्यालय में क्लस्टर पंजीकरण हेतु संपर्क करें।",

                official_url="https://pgsindia-ncof.gov.in",

                is_active=True,

            ),

        ]

        db.session.add_all(schemes)

        db.session.commit()



    if Article.query.count() == 0:

        admin = User.query.filter_by(role="admin").first()

        author_id = admin.id if admin else None

        articles = [

            Article(

                title="गेहूं की फसल में कल्ले बढ़ाने और बंपर पैदावार के वैज्ञानिक उपाय",

                category="फसल प्रबंधन (Crop Management)",

                language="Hindi",

                author_id=author_id,

                content="गेहूं की अच्छी पैदावार के लिए पहली सिंचाई (बुवाई के 20-22 दिन बाद, CRI स्टेज) सबसे महत्वपूर्ण होती है। इस समय ज्यादा पानी न भरें बल्कि हल्की सिंचाई करें। सिंचाई के 3-4 दिन बाद प्रति एकड़ 45 किग्रा यूरिया के साथ 5 किग्रा जिंक सल्फेट (33%) जरूर डालें।\n\nकल्ले फूटते समय यदि नैनो यूरिया (4 मिली प्रति लीटर पानी) का छिड़काव किया जाए तो कल्लों की संख्या 25-30% तक बढ़ जाती है। यदि खरपतवार हों तो 30-35 दिन की अवस्था पर उचित खरपतवारनाशक का प्रयोग करें।",

            ),

            Article(

                title="घर पर जैविक कीटनाशक 'नीमास्त्र' और 'दशपर्णी अर्क' बनाने की सरल विधि",

                category="जैविक खेती (Organic Farming)",

                language="Hindi",

                author_id=author_id,

                content="रासायनिक कीटनाशकों के अत्यधिक खर्च और मिट्टी के नुकसान से बचने के लिए नीमास्त्र एक अचूक प्राकृतिक समाधान है।\n\nआवश्यक सामग्री:\n1. 5 किग्रा नीम की पत्तियां या निंबोली\n2. 5 लीटर देसी गाय का ताजा गोमूत्र\n3. 2 किग्रा ताजा गाय का गोबर\n4. 100 लीटर पानी\n\nबनाने की विधि:\nसभी सामग्रियों को एक बड़े प्लास्टिक ड्रम में डंडे से अच्छी तरह मिला लें। इसे छायादार स्थान पर कपड़े से ढककर 48 घंटे के लिए रखें। सुबह और शाम 2 मिनट घड़ी की दिशा में हिलाएं। 48 घंटे बाद इसे छान लें। यह 1 एकड़ फसल में रस चूसक कीड़ों (माहू, सफेद मक्खी) और सुंडियों की रोकथाम के लिए पर्याप्त है।",

            ),

            Article(

                title="ड्रिप सिंचाई (टपक सिंचाई) तकनीक: 50% पानी की बचत और 40% अधिक उत्पादन",

                category="सिंचाई तकनीक (Irrigation)",

                language="Hindi",

                author_id=author_id,

                content="पारंपरिक नाली सिंचाई में लगभग 60% पानी भाप बनकर या मिट्टी में बहकर व्यर्थ हो जाता है। ड्रिप सिंचाई प्रणाली द्वारा पानी और घुलनशील उर्वरक (Fertigation) सीधे पौधों की जड़ों में बूंद-बूंद करके दिए जाते हैं।\n\nप्रमुख लाभ:\n• पानी की 50-60% तक बचत\n• खरपतवारों का 70% कम होना\n• सब्जियों (टमाटर, मिर्च, शिमला मिर्च) और फलों में फल की गुणवत्ता बेहतरीन\n• बिजली और मजदूरी के खर्च में भारी कमी\nवर्तमान में राज्य सरकारें ड्रिप और मिनी स्प्रिंकलर लगाने पर 70% से 80% तक का अनुदान दे रही हैं।",

            ),

            Article(

                title="वर्मीकम्पोस्ट (केंचुआ खाद) तैयार करने की वैज्ञानिक विधि",

                category="जैविक खाद (Organic Manure)",

                language="Hindi",

                author_id=author_id,

                content="केंचुआ खाद साधारण गोबर की खाद से 5 गुना अधिक नाइट्रोजन, 8 गुना अधिक फास्फोरस और 11 गुना अधिक पोटाश प्रदान करती है।\n\nविधि:\n1. शेड या छायादार स्थान पर 30 फीट लंबा, 3 फीट चौड़ा और 2 फीट ऊंचा बेड बनाएं।\n2. सबसे नीचे सूखी पत्तियां या पुआल की 3 इंच परत बिछाएं।\n3. इसके ऊपर 15-20 दिन पुराना ठंडा गोबर और फसल अवशेष भरें।\n4. ऑस्ट्रेलियन केंचुए (Eisenia Fetida) प्रति बेड 3-4 किग्रा छोड़ें और नमी 40% बनाए रखने के लिए हल्का पानी छिड़कें।\n5. बोरी से ढक दें। 45-60 दिनों में चाय पत्ती जैसी महक रहित दानेदार वर्मीकम्पोस्ट तैयार हो जाती है।",

            ),

            Article(

                title="Modern Integrated Pest Management (IPM) Best Practices",

                category="Crop Protection",

                language="English",

                author_id=author_id,

                content="Integrated Pest Management (IPM) is an environmentally friendly approach combining multiple pest control methods:\n\n1. Field Monitoring: Inspect crops twice weekly to catch pest build-ups before they reach Economic Threshold Levels (ETL).\n2. Mechanical Traps: Install 10-12 Yellow Sticky Traps per acre for sucking pests (aphids, whiteflies) and Pheromone Traps for fruit and shoot borers.\n3. Biological Controls: Use Trichoderma viride for soil-borne fungal diseases and Pseudomonas fluorescens for seed treatment.\n4. Balanced Fertilization: Avoid excessive nitrogenous fertilizers, as lush soft growth attracts aphids and sap-sucking insects.",

            ),

            Article(

                title="सरसों की फसल में माहू (चेपा) कीट से बचाव और उचित पोषण",

                category="कीट नियंत्रण (Pest Control)",

                language="Hindi",

                author_id=author_id,

                content="सरसों में फूल आने और फलियां बनते समय जब आसमान में बादल छाए रहते हैं या तापमान बढ़ता है, तब माहू कीट का भारी हमला होता है। यह कीट फूलों और फलियों का रस चूस लेता है जिससे दाना पतला रह जाता है।\n\nरोकथाम:\n• शुरुआती प्रकोप पर खेत में पीली चिपचिपी पट्टियां लगाएं।\n• नीम तेल (1500 PPM) 5 मिली प्रति लीटर पानी में मिलाकर छिड़कें।\n• गंभीर स्थिति में इमिडाक्लोप्रिड 17.8 SL (1 मिली प्रति 3 लीटर पानी) का छिड़काव करें।\n• दाना भरते समय घुलनशील पोटाश (00:00:50) का 1% छिड़काव करने से दानों में चमक और तेल की मात्रा बढ़ती है।",

            ),

        ]

        db.session.add_all(articles)

        db.session.commit()



    if Crop.query.count() == 0:

        farmer = User.query.filter_by(role="farmer").first()

        if not farmer:

            farmer = User(

                name="Rameshwar Sharma",

                email="rameshwar.farmer@kisansetu.in",

                role="farmer",

                phone="9876543210",

                village="Rampur",

                district="Karnal",

                state="Haryana",

            )

            farmer.set_password("Farmer@12345")

            db.session.add(farmer)

            db.session.commit()



        crops = [

            Crop(

                farmer_id=farmer.id,

                name="Sharbati Wheat (शरबती गेहूं - MP)",

                quantity=45.0,

                unit="quintal",

                price_per_unit=2650.0,

                quality="Premium",

                description="शुद्ध शरबती गेहूं, प्राकृतिक रूप से उगाया गया, पूरी तरह से साफ एवं सुखाया हुआ। रोटियां अत्यधिक मुलायम और स्वादिष्ट बनती हैं।",

                status="active",

            ),

            Crop(

                farmer_id=farmer.id,

                name="Basmati Paddy 1121 (बासमती धान)",

                quantity=35.0,

                unit="quintal",

                price_per_unit=3900.0,

                quality="Premium",

                description="प्रमाणित 1121 बासमती धान, खेत से सीधे उपलब्ध। लंबा दाना और उत्कृष्ट प्राकृतिक सुगंध। नमी 12% से कम।",

                status="active",

            ),

            Crop(

                farmer_id=farmer.id,

                name="Organic Yellow Mustard (पीली सरसों)",

                quantity=18.0,

                unit="quintal",

                price_per_unit=5450.0,

                quality="Good",

                description="बिना रासायनिक कीटनाशक के उगाई गई शुद्ध पीली सरसों। उच्च तेल प्रतिशत (42%+)। थोक एवं मिल खरीदारों के लिए उत्तम।",

                status="active",

            ),

            Crop(

                farmer_id=farmer.id,

                name="Farm Fresh Desi Tomatoes (देसी टमाटर)",

                quantity=600.0,

                unit="kg",

                price_per_unit=24.0,

                quality="Standard",

                description="खेत से आज ही तोड़े गए ताजा, लाल और ठोस देसी टमाटर। सब्जी मंडियों, होटल और रिटेल खरीदारों के लिए तैयार।",

                status="active",

            ),

            Crop(

                farmer_id=farmer.id,

                name="Chandramukhi Potatoes (आलू)",

                quantity=80.0,

                unit="quintal",

                price_per_unit=1200.0,

                quality="Standard",

                description="अच्छे आकार के चंद्रमुखी आलू। बिना दाग-धब्बे के, सीधे फार्महाउस से उचित दाम पर उपलब्ध।",

                status="active",

            ),

        ]

        db.session.add_all(crops)

        db.session.commit()



    if not User.query.filter_by(role="buyer").first():

        buyer = User(

            name="Vikram Agro Traders",

            email="buyer@kisansetu.in",

            role="buyer",

            phone="9812345678",

            village="Mandi Road",

            district="Delhi NCR",

            state="Delhi",

        )

        buyer.set_password("Buyer@12345")

        db.session.add(buyer)

        db.session.commit()



        crop = Crop.query.first()

        farmer = User.query.filter_by(role="farmer").first()

        if crop and farmer:

            order = Order(

                crop_id=crop.id,

                buyer_id=buyer.id,

                farmer_id=farmer.id,

                quantity=5.0,

                price_per_unit=crop.price_per_unit,

                total_amount=round(5.0 * crop.price_per_unit, 2),

                status="pending",

            )

            db.session.add(order)

            db.session.commit()





# -------------------- DATABASE INITIALIZATION --------------------

with app.app_context():
    os.makedirs(app.instance_path, exist_ok=True)
    db.create_all()

    admin_email = os.environ.get(
        "ADMIN_EMAIL",
        "admin@kisansetu.in",
    ).strip().lower()

    admin_password = os.environ.get(
        "ADMIN_PASSWORD",
        "Admin@12345",
    )

    if not User.query.filter_by(role="admin").first():
        admin = User(
            name="KisanSetu Admin",
            email=admin_email,
            role="admin",
        )

        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()

    seed_initial_data()


if __name__ == "__main__":
    app.run(debug=True)
