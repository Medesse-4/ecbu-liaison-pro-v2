# Mise à jour professionnelle ciblée — ECBU Liaison Pro V2

Cette archive ne reprend pas le projet de zéro. Elle applique uniquement les corrections demandées :

- fiche de demande ECBU enrichie pour le clinicien ;
- contrôle automatique de conformité pré-analytique à la réception ;
- bon de résultat plus professionnel, sans phrases non adaptées ;
- vocabulaire administrateur nettoyé ;
- renforcement des en-têtes de sécurité ;
- conservation des données sur Render via PostgreSQL obligatoire.

## Fichiers principalement modifiés

- `app/models.py`
- `app/forms.py`
- `app/requests/routes.py`
- `app/samples/routes.py`
- `app/templates/requests/form.html`
- `app/templates/samples/form.html`
- `app/templates/results/report.html`
- `app/templates/admin/users.html`
- `app/static/css/app.css`
- `app/__init__.py`
- `config.py`

## Mise à jour locale

1. Remplacer les fichiers du projet par ceux de cette archive.
2. Tester localement :

```powershell
python -m compileall app run.py config.py extensions.py
python run.py
```

3. Envoyer vers GitHub :

```powershell
git add .
git commit -m "Ameliore demande conformite securite et bon resultat"
git push
```

## Important pour Render

Pour éviter la perte des comptes et données après redémarrage, Render doit utiliser PostgreSQL.
Ne pas utiliser SQLite en production.

Variable obligatoire sur Render :

```text
DATABASE_URL = valeur PostgreSQL fournie par Render
```

Les autres variables obligatoires :

```text
SECRET_KEY
ADMIN_EMAIL
ADMIN_PASSWORD
FLASK_ENV=production
SECURE_COOKIES=true
```
