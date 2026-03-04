import configuration
import installation
import server
import models
import gunicorn.config


application = server.application


with application.app_context():
    models.auto_update()
    installation.install_dirs()
    installation.install_admin()
    installation.delete_expired_sessions()


if __name__ == "__main__":
    application.run(debug=True)

