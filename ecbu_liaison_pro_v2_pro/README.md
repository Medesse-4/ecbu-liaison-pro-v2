# ECBU Liaison Pro V2

Plateforme LIMS modulaire pour ECBU, qualité pré-analytique, non-conformités, CAPA, antibiorésistance et statistiques scientifiques.

## Lancement local Windows / VS Code

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Ouvrir : http://127.0.0.1:5000

Par défaut local, si `DATABASE_URL` n'est pas configuré, l'application utilise SQLite dans `instance/dev.db` pour tester. En production, PostgreSQL est obligatoire.

## Render

Variables obligatoires :

- SECRET_KEY
- DATABASE_URL
- ADMIN_EMAIL
- ADMIN_PASSWORD
- MAIL_*
- REDIS_URL si Celery/Redis activé

Start command :

```bash
gunicorn 'app:create_app()' --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
```

## Modules

- Authentification sécurisée Argon2, CSRF, Flask-Login, rate limiting
- Validation email + activation admin
- Demandes ECBU
- Échantillons avec QR code logique
- Résultats biologiques
- Antibiogrammes EUCAST
- Non-conformités et CAPA
- Statistiques mémoire
- Dashboard qualité, activité, microbiologie, antibiorésistance
- Tickets support
- Notifications internes et email
- Audit append-only avec chaînage hash
- Exports CSV, Excel, PDF
