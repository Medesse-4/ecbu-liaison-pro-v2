from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

ROLES = [("prescripteur", "Prescripteur"), ("laboratoire", "Laboratoire"), ("chef_labo", "Chef laboratoire"), ("responsable_qualite", "Responsable qualité")]

class LoginForm(FlaskForm):
    email = StringField("Email professionnel", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Connexion")

class RegisterForm(FlaskForm):
    name = StringField("Nom complet", validators=[DataRequired(), Length(min=3, max=160)])
    email = StringField("Email professionnel", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=10)])
    confirm = PasswordField("Confirmation", validators=[DataRequired(), EqualTo("password")])
    role = SelectField("Profil", choices=ROLES, validators=[DataRequired()])
    service = StringField("Service", validators=[DataRequired(), Length(max=160)])
    submit = SubmitField("Créer le compte")

class RequestForm(FlaskForm):
    sampling_code = StringField("Code prélèvement", validators=[Optional(), Length(max=80)])
    patient_code = StringField("Code patient", validators=[Optional(), Length(max=80)])
    patient_name = StringField("Nom patient", validators=[DataRequired(), Length(max=120)])
    patient_firstname = StringField("Prénoms patient", validators=[Optional(), Length(max=160)])
    patient_age = StringField("Âge", validators=[Optional(), Length(max=20)])
    patient_age_unit = SelectField("Unité", choices=[("ans","Ans"),("mois","Mois"),("jours","Jours")])
    patient_sex = SelectField("Sexe", choices=[("M","Masculin"),("F","Féminin")])
    patient_phone = StringField("Téléphone", validators=[Optional(), Length(max=40)])
    requesting_service = StringField("Service demandeur", validators=[DataRequired(), Length(max=160)])
    prescriber_name = StringField("Médecin prescripteur", validators=[DataRequired(), Length(max=160)])
    clinical_context = TextAreaField("Contexte clinique", validators=[Optional()])
    urgent = BooleanField("Urgent")
    submit = SubmitField("Enregistrer")

class SampleForm(FlaskForm):
    sample_number = StringField("N° échantillon", validators=[DataRequired(), Length(max=60)])
    sample_type = SelectField("Type", choices=[("jet_moyen","Jet moyen"),("sonde","Sonde"),("poche","Poche collectrice"),("autre","Autre")])
    sampling_date = DateField("Date prélèvement", validators=[Optional()])
    sampling_time = TimeField("Heure prélèvement", validators=[Optional()])
    reception_date = DateField("Date réception", validators=[Optional()])
    reception_time = TimeField("Heure réception", validators=[Optional()])
    transport_condition = StringField("Transport", validators=[Optional(), Length(max=160)])
    storage_temperature = StringField("Température", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Enregistrer")

class ResultForm(FlaskForm):
    aspect = StringField("Aspect", validators=[Optional(), Length(max=160)])
    leukocytes = StringField("Leucocytes", validators=[Optional(), Length(max=80)])
    red_cells = StringField("Hématies", validators=[Optional(), Length(max=80)])
    epithelial_cells = StringField("Cellules épithéliales", validators=[Optional(), Length(max=160)])
    other_elements = TextAreaField("Autres éléments", validators=[Optional()])
    gram_stain = TextAreaField("Coloration de Gram", validators=[Optional()])
    culture_status = SelectField("Culture", choices=[("positive","Positive"),("negative","Négative"),("contaminated","Contaminée"),("rejected","Rejetée")])
    culture_details = TextAreaField("Détails culture", validators=[Optional()])
    conclusion = TextAreaField("Conclusion", validators=[Optional()])
    submit = SubmitField("Enregistrer")

class NonConformityForm(FlaskForm):
    type_nc = SelectField("Type", choices=[("mauvaise_identification","Mauvaise identification"),("volume_insuffisant","Volume insuffisant"),("pot_non_conforme","Pot non conforme"),("contamination","Contamination"),("retard_acheminement","Retard d’acheminement"),("erreur_transport","Erreur de transport"),("demande_incomplete","Demande incomplète"),("discordance","Discordance patient-échantillon")])
    severity = SelectField("Gravité", choices=[("faible","Faible"),("moderee","Modérée"),("elevee","Élevée"),("critique","Critique")])
    impact = StringField("Impact", validators=[Optional(), Length(max=80)])
    consequence = TextAreaField("Conséquence", validators=[Optional()])
    decision = TextAreaField("Décision", validators=[Optional()])
    responsible = StringField("Responsable", validators=[Optional(), Length(max=160)])
    submit = SubmitField("Déclarer")

class TicketForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired(), Length(max=180)])
    category = SelectField("Catégorie", choices=[("erreur","Erreur"),("assistance","Assistance"),("suggestion","Suggestion")])
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Envoyer")
