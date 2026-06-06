import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, render_template
from sqlalchemy import text
from config import Config, ProductionConfig
from extensions import db, migrate, csrf, login_manager, limiter, mail, swagger


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object or Config)
    if app.config.get("ENV") == "production":
        ProductionConfig.validate()

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    handler = RotatingFileHandler("logs/ecbu_liaison_pro.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Veuillez vous connecter."

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    register_blueprints(app)
    register_errors(app)

    with app.app_context():
        db.create_all()
        ensure_runtime_schema(app)
        seed_admin(app)

    return app


def register_blueprints(app):
    from app.auth.routes import bp as auth_bp
    from app.dashboard.routes import bp as dashboard_bp
    from app.admin.routes import bp as admin_bp
    from app.requests.routes import bp as requests_bp
    from app.samples.routes import bp as samples_bp
    from app.results.routes import bp as results_bp
    from app.quality.routes import bp as quality_bp
    from app.statistics.routes import bp as statistics_bp
    from app.antibiograms.routes import bp as antibiograms_bp
    from app.tickets.routes import bp as tickets_bp
    from app.notifications.routes import bp as notifications_bp
    from app.audit.routes import bp as audit_bp
    from app.api.routes import bp as api_bp
    for bp in [auth_bp, dashboard_bp, admin_bp, requests_bp, samples_bp, results_bp, quality_bp, statistics_bp, antibiograms_bp, tickets_bp, notifications_bp, audit_bp, api_bp]:
        app.register_blueprint(bp)


def register_errors(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal(error):
        app.logger.exception("Erreur serveur")
        return render_template("errors/500.html"), 500


def seed_admin(app):
    from app.models import User
    from app.security import hash_password
    email = app.config["ADMIN_EMAIL"].lower().strip()
    password = app.config["ADMIN_PASSWORD"]
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(name="Administrateur", email=email, role="admin", service="Administration", is_active=True, is_email_verified=True, is_admin_approved=True, password_hash=hash_password(password))
        db.session.add(user)
        db.session.commit()


def ensure_runtime_schema(app):
    """Ajoute les colonnes non destructives nécessaires si une base locale existait déjà."""
    engine = db.engine
    inspector = db.inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("users")}
    additions = {
        "deletion_requested_at": "DATETIME",
        "deletion_reason": "TEXT",
        "deletion_confirmed_by_id": "INTEGER",
        "deletion_confirmed_at": "DATETIME",
    }
    with engine.begin() as conn:
        for col, ddl in additions.items():
            if col not in cols:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))

    table_additions = {
        "ecbu_requests": {
            "deleted_by_id": "INTEGER",
            "delete_reason": "TEXT",
        },
        "lab_results": {
            "deleted_at": "DATETIME",
            "deleted_by_id": "INTEGER",
            "delete_reason": "TEXT",
        },
    }
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, wanted in table_additions.items():
            if table not in tables:
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col, ddl in wanted.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
