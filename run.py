import getpass
import os
import socket
import sys

from dotenv import load_dotenv
from flask_mail import Message

from backend.apps import create_app
from backend.models import PlatformAdmin, db

load_dotenv()
app = create_app()


def find_available_port(start_port=5000):
    """Find the next available port starting from start_port."""
    port = start_port
    while port < 65535:  # Max port number
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No available ports found")


def _create_super_admin_interactive():
    print("\n" + "=" * 60)
    print("CREATION SUPER ADMIN TEKANAYO APP")
    print("=" * 60)

    while True:
        first_name = input("Prénom: ").strip()
        if first_name:
            break
        print("Le prénom est obligatoire.")

    while True:
        last_name = input("Nom: ").strip()
        if last_name:
            break
        print("Le nom est obligatoire.")

    while True:
        email = input("Email: ").strip().lower()
        if email and "@" in email:
            break
        print("Email invalide.")

    while True:
        password = getpass.getpass("Mot de passe: ").strip()
        if len(password) < 6:
            print("Le mot de passe doit faire au moins 6 caractères.")
            continue
        confirm = getpass.getpass("Confirmer mot de passe: ").strip()
        if password == confirm:
            break
        print("Les mots de passe ne correspondent pas.")

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
    }


def _create_super_admin_from_env():
    first_name = (os.getenv("SUPERADMIN_FIRST_NAME") or "").strip()
    last_name = (os.getenv("SUPERADMIN_LAST_NAME") or "").strip()
    email = (os.getenv("SUPERADMIN_EMAIL") or "").strip().lower()
    password = (os.getenv("SUPERADMIN_PASSWORD") or "").strip()

    if not all([first_name, last_name, email, password]):
        return None
    if "@" not in email or len(password) < 6:
        return None

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
    }


def _get_super_admin_data():
    if sys.stdin.isatty():
        try:
            return _create_super_admin_interactive()
        except (KeyboardInterrupt, EOFError):
            print("\nCréation du super admin annulée.")
            return None

    data = _create_super_admin_from_env()
    if data:
        print("Super admin chargé depuis .env")
        return data

    print("Terminal non interactif: définissez SUPERADMIN_* dans .env")
    return None


def ensure_super_admin():
    with app.app_context():
        existing_super_admin = PlatformAdmin.query.filter_by(role="super_admin").first()
        if existing_super_admin:
            return

        admin_data = _get_super_admin_data()
        if not admin_data:
            return

        existing_by_email = PlatformAdmin.query.filter_by(email=admin_data["email"]).first()
        if existing_by_email:
            admin = existing_by_email
            admin.first_name = admin_data["first_name"]
            admin.last_name = admin_data["last_name"]
            admin.role = "super_admin"
            admin.is_active = True
            admin.permissions = "manage_sellers,manage_subscriptions,manage_announcements,manage_admins,manage_settings"
        else:
            admin = PlatformAdmin(
                email=admin_data["email"],
                first_name=admin_data["first_name"],
                last_name=admin_data["last_name"],
                role="super_admin",
                permissions="manage_sellers,manage_subscriptions,manage_announcements,manage_admins,manage_settings",
                is_active=True,
            )
            db.session.add(admin)

        admin.set_password(admin_data["password"])
        db.session.commit()

        print("\n" + "=" * 60)
        print("SUPER ADMIN CREE AVEC SUCCES")
        print("=" * 60)
        print(f"Nom: {admin.first_name} {admin.last_name}")
        print(f"Email: {admin.email}")
        print("=" * 60)

        try:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; font-weight: bold; }}
                    .content {{ padding: 40px 30px; }}
                    .greeting {{ color: #333; font-size: 16px; margin-bottom: 20px; }}
                    .greeting strong {{ color: #667eea; }}
                    .section {{ margin: 30px 0; }}
                    .section-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 15px; }}
                    .link-list {{ list-style: none; padding: 0; margin: 0; }}
                    .link-list li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                    .link-list li:last-child {{ border-bottom: none; }}
                    .link-list a {{ color: #667eea; text-decoration: none; font-weight: 500; display: flex; align-items: center; font-size: 15px; }}
                    .link-list a:hover {{ text-decoration: underline; }}
                    .link-list i {{ margin-right: 10px; }}
                    .cta-button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; text-align: center; margin: 20px 0; }}
                    .cta-button:hover {{ opacity: 0.9; }}
                    .divider {{ height: 2px; background: linear-gradient(90deg, #667eea, #764ba2); margin: 30px 0; }}
                    .footer {{ background: #f5f5f5; padding: 20px; text-align: center; color: #666; font-size: 13px; border-top: 1px solid #ddd; }}
                    .footer p {{ margin: 5px 0; }}
                    .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; color: #856404; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Bienvenue Super Admin!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Tekanayo App</p>
                    </div>
                    <div class="content">
                        <div class="greeting">
                            Bonjour <strong>{admin.first_name} {admin.last_name}</strong>,
                        </div>
                        <p style="color: #666; line-height: 1.6; margin: 15px 0;">
                            Votre compte Super Admin Tekanayo App a été créé avec succès! 
                            Vous avez maintenant accès complet à la gestion de la plateforme.
                        </p>
                        
                        <div class="divider"></div>
                        
                        <div class="section">
                            <div class="section-title">📍 Accès aux différentes interfaces</div>
                            <ul class="link-list">
                                <li><a href="http://localhost:5000/admin">⚙️ Tableau de bord Admin</a></li>
                                <li><a href="http://localhost:5000">🌐 Portail Client</a></li>
                                <li><a href="http://localhost:5000/vendeur/register">🛍️ Enregistrement Vendeur</a></li>
                                <li><a href="http://localhost:5000/vendeur">👤 Espace Vendeur</a></li>
                                <li><a href="http://localhost:5000/livreur">🚚 Interface Livreur</a></li>
                                <li><a href="http://localhost:5000/boutique1">🏪 Exemple Boutique</a></li>
                            </ul>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">🔐 Vos identifiants</div>
                            <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
                                <p style="margin: 5px 0;"><strong>Email:</strong> {admin.email}</p>
                                <p style="margin: 5px 0;"><strong>Rôle:</strong> Super Admin</p>
                                <p style="margin: 5px 0;"><strong>Permissions:</strong> Accès complet à la plateforme</p>
                            </div>
                        </div>
                        
                        <a href="http://localhost:5000/admin" class="cta-button">Accéder au Tableau de Bord Admin</a>
                        
                        <div class="alert">
                            <strong>⚠️ Important:</strong> Ne partagez jamais vos identifiants. 
                            Changez votre mot de passe lors de votre première connexion.
                        </div>
                        
                        <div class="section">
                            <div class="section-title">💡 Prochaines étapes</div>
                            <ol style="color: #666; line-height: 1.8; padding-left: 20px;">
                                <li>Connectez-vous au tableau de bord admin</li>
                                <li>Configurez les paramètres de la plateforme</li>
                                <li>Examinez les demandes d'enregistrement de vendeurs</li>
                                <li>Gérez les annonces et promotions</li>
                                <li>Supervisez les transactions</li>
                            </ol>
                        </div>
                    </div>
                    <div class="footer">
                        <p><strong>Tekanayo App</strong> - Plateforme e-commerce avancée</p>
                        <p>Propulsé par Esperdigi | Tous droits réservés © 2024-2026</p>
                        <p>Pour toute assistance, veuillez contacter le support technique.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            msg = Message(
                subject="🎉 Votre compte Super Admin Tekanayo App a été créé!",
                sender=app.config.get("MAIL_DEFAULT_SENDER"),
                recipients=[admin.email],
                html=html,
            )
            app.extensions["mail"].send(msg)
        except Exception:
            pass


def print_ready_banner(port=5000):
    print("=" * 50)
    print("🎯 TekanayoApp - PRÊT À FONCTIONNER!")
    print("=" * 50)
    print(f"🌐 URL Client: http://localhost:{port} ")
    print(f"⚙️  URL Admin: http://localhost:{port}/admin ")
    print(f"🚚 URL Livreur: http://localhost:{port}/livreur ")
    print(f"🛍️ URL Vendeur: http://localhost:{port}/vendeur ")
    print(f"🏪 URL Boutique: http://localhost:{port}/boutique1 ")
    print("📧 Emails: Activés avec Gmail SMTP")
    print("=" * 36)


if __name__ == "__main__":
    ensure_super_admin()
    # Forcer l'utilisation du port 5000
    port = 5000
    print_ready_banner(port)
    use_debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(debug=use_debug, port=port)

