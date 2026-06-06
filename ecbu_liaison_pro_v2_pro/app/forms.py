from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

ROLES = [
    ("prescripteur", "Prescripteur"),
    ("laboratoire", "Laboratoire"),
    ("chef_labo", "Chef laboratoire"),
]

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
    patient_name = StringField("Nom", validators=[DataRequired(), Length(max=120)])
    patient_firstname = StringField("Prénoms", validators=[DataRequired(), Length(max=160)])
    patient_sex = SelectField("Sexe", choices=[("M","Masculin"),("F","Féminin")], validators=[DataRequired()])
    patient_age = StringField("Âge", validators=[DataRequired(), Length(max=20)])
    patient_age_unit = SelectField("Unité d’âge", choices=[("ans","Ans"),("mois","Mois"),("jours","Jours")])
    hospital_origin = StringField("Hôpital de provenance", validators=[DataRequired(), Length(max=180)])
    origin_commune = StringField("Provenance / commune", validators=[DataRequired(), Length(max=160)])
    requesting_service = StringField("Service", validators=[DataRequired(), Length(max=160)])
    prescriber_name = StringField("Médecin prescripteur", validators=[DataRequired(), Length(max=160)])
    sample_nature = SelectField("Nature du prélèvement", choices=[("urines_jet_moyen","Urines - jet moyen"),("urines_sonde","Urines sur sonde"),("urines_poche","Urines - poche collectrice"),("autre","Autre")], validators=[DataRequired()])
    patient_under_catheter = BooleanField("Patient sous sonde")
    consultation_reason = TextAreaField("Motif de consultation", validators=[DataRequired()])
    general_signs = TextAreaField("Signes généraux", validators=[Optional()])
    recent_hospitalization_before_admission = SelectField("Hospitalisation récente avant admission ?", choices=[("non","Non"),("oui","Oui"),("non_renseigne","Non renseigné")])
    recent_hospitalization_duration = StringField("Durée du séjour récent", validators=[Optional(), Length(max=80)])
    currently_hospitalized = SelectField("Hospitalisé actuellement ?", choices=[("non","Non"),("oui","Oui"),("non_renseigne","Non renseigné")])
    current_hospitalization_duration = StringField("Durée d’hospitalisation actuelle", validators=[Optional(), Length(max=80)])
    antibiotic_treatment = SelectField("Traitement antibiotique", choices=[("non","Non"),("oui","Oui"),("non_renseigne","Non renseigné")])
    current_atb_duration = StringField("Durée du traitement ATB en cours", validators=[Optional(), Length(max=80)])
    chronic_disease = TextAreaField("Maladie chronique sous-jacente", validators=[Optional()])
    primary_diagnosis = TextAreaField("Diagnostic principal", validators=[DataRequired()])
    sampling_date = DateField("Date de prélèvement", validators=[DataRequired()])
    urgent = BooleanField("Demande urgente")
    submit = SubmitField("Envoyer au laboratoire")

class SampleForm(FlaskForm):
    sample_number = StringField("N° échantillon", validators=[DataRequired(), Length(max=60)])
    sample_type = SelectField("Nature reçue", choices=[("jet_moyen","Urines - jet moyen"),("sonde","Urines sur sonde"),("poche","Urines - poche collectrice"),("autre","Autre")])
    sampling_date = DateField("Date prélèvement", validators=[Optional()])
    sampling_time = TimeField("Heure prélèvement", validators=[Optional()])
    reception_date = DateField("Date réception", validators=[Optional()])
    reception_time = TimeField("Heure réception", validators=[Optional()])
    transport_condition = StringField("Conditions de transport", validators=[Optional(), Length(max=160)])
    storage_temperature = StringField("Température / conservation", validators=[Optional(), Length(max=80)])
    patient_informed = BooleanField("Patient informé des conditions de prélèvement")
    technique_mastered = BooleanField("Technique de prélèvement maîtrisée")
    intimate_toilet = BooleanField("Toilette intime réalisée")
    sterile_container = BooleanField("Flacon stérile utilisé")
    identified_container = BooleanField("Flacon correctement identifié")
    sufficient_volume = BooleanField("Volume suffisant")
    no_leakage = BooleanField("Absence de fuite / flacon non souillé")
    delay_compliant = BooleanField("Délai prélèvement-réception conforme")
    temperature_compliant = BooleanField("Température conforme")
    transport_compliant = BooleanField("Transport conforme")
    sample_nature_compliant = BooleanField("Nature du prélèvement conforme")
    collection_instructions_given = BooleanField("Consignes de prélèvement disponibles et cohérentes")
    request_form_complete = BooleanField("Fiche de demande complète")
    patient_identity_match = BooleanField("Identité patient conforme demande/flacon")
    acceptable_container = BooleanField("Contenant adapté à l’examen demandé")
    preanalytical_comment = TextAreaField("Observation de réception", validators=[Optional()])
    submit = SubmitField("Enregistrer la réception")

class ResultForm(FlaskForm):
    lab_name = StringField("Nom du laboratoire sur le bon", validators=[Optional(), Length(max=180)])
    aspect = StringField("Aspect", validators=[Optional(), Length(max=160)])
    leukocytes = StringField("Leucocytes", validators=[Optional(), Length(max=80)])
    red_cells = StringField("Hématies", validators=[Optional(), Length(max=80)])
    epithelial_cells = StringField("Cellules épithéliales", validators=[Optional(), Length(max=160)])
    other_elements = TextAreaField("Autres éléments", validators=[Optional()])
    gram_stain = TextAreaField("Coloration de Gram", validators=[Optional()])
    culture_status = SelectField("Culture", choices=[("positive","Positive"),("negative","Négative"),("contaminated","Contaminée"),("rejected","Rejetée")])
    culture_details = TextAreaField("Germe isolé / détails culture", validators=[Optional()])
    rejection_reason = TextAreaField("Motif de rejet du prélèvement", validators=[Optional()])
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
