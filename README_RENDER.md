# Déploiement Render — ECBU Liaison Pro V2

## 1. Variables obligatoires sur Render

- `DATABASE_URL` : fournie par la base PostgreSQL Render
- `SECRET_KEY` : longue clé aléatoire
- `ADMIN_EMAIL` : email du premier administrateur
- `ADMIN_PASSWORD` : mot de passe fort du premier administrateur
- `SECURE_COOKIES=true`

## 2. Commandes Render

Build Command :

```bash
pip install -r requirements.txt
```

Start Command :

```bash
gunicorn 'app:create_app()' --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
```

## 3. Règles intégrées

- Pas de double authentification.
- Un utilisateur inscrit attend uniquement la validation administrateur.
- L’administrateur gère le site, les comptes, suggestions, sécurité et réinitialisation.
- L’administrateur ne dispose d’aucun module clinique, laboratoire, qualité clinique, résultat ou antibiorésistance.
- Le prescripteur voit uniquement ses demandes et résultats validés.
- Le laboratoire/chef laboratoire accède aux modules de laboratoire, résultats, antibiogrammes et statistiques antibiorésistance.
