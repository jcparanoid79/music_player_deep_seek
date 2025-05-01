import os

from flask import Flask

from .routes import bp


def create_app():
    # Get absolute path to src directory
    src_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(src_dir, "templates")
    static_dir = os.path.join(src_dir, "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
    )

    # Enable debug mode
    app.config["DEBUG"] = True

    # Debug print template info
    print(f"Template directory: {template_dir}")
    print(
        f"Template file exists: {os.path.exists(os.path.join(template_dir, 'player.html'))}"
    )

    app.register_blueprint(bp)
    return app
