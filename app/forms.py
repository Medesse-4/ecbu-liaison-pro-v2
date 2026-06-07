from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

ROLES = [("prescripteur", "Prescripteur"), ("laboratoire", "Laboratoire")]

YES_NO = [("non", "Non"), ("oui", "Oui"), ("non_renseigne", "Non renseigné")]

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


class LabProfileForm(FlaskForm):
    hospital_name = StringField("Nom de l’hôpital", validators=[DataRequired(), Length(max=180)])
    laboratory_name = StringField("Nom du laboratoire", validators=[DataRequired(), Length(max=180)])
    validator_title = StringField("Titre du validateur", validators=[Optional(), Length(max=120)])
    signature_text = StringField("Signature électronique à afficher", validators=[Optional(), Length(max=160)])
    submit = SubmitField("Enregistrer les paramètres du bon")

class RequestForm(FlaskForm):
    sampling_code = StringField("Code prélèvement", validators=[Optional(), Length(max=80)])
    patient_code = StringField("Code patient", validators=[Optional(), Length(max=80)])
    patient_name = StringField("Nom", validators=[DataRequired(), Length(max=120)])
    patient_firstname = StringField("Prénoms", validators=[DataRequired(), Length(max=160)])
    patient_age = StringField("Âge", validators=[DataRequired(), Length(max=20)])
    patient_age_unit = SelectField("Unité", choices=[("ans","Ans"),("mois","Mois"),("jours","Jours")])
    patient_sex = SelectField("Sexe", choices=[("M","Masculin"),("F","Féminin")])
    patient_phone = StringField("Téléphone", validators=[Optional(), Length(max=40)])
    hospital_name = StringField("Hôpital de provenance", validators=[DataRequired(), Length(max=180)])
    requesting_service = StringField("Service", validators=[DataRequired(), Length(max=160)])
    origin_commune = StringField("Provenance / commune", validators=[Optional(), Length(max=160)])
    sample_nature = SelectField("Nature du prélèvement", choices=[("urines", "Urines"), ("urines_sonde", "Urines sur sonde"), ("autre", "Autre")])
    patient_probe = SelectField("Patient sous sonde", choices=YES_NO)
    consultation_reason = TextAreaField("Motif de consultation", validators=[Optional()])
    general_signs = TextAreaField("Signes généraux", validators=[Optional()])
    recent_hospitalization = SelectField("Hospitalisation récente avant admission", choices=YES_NO)
    recent_hospitalization_duration = StringField("Durée de séjour", validators=[Optional(), Length(max=80)])
    currently_hospitalized = SelectField("Hospitalisé actuellement", choices=YES_NO)
    current_hospitalization_duration = StringField("Durée", validators=[Optional(), Length(max=80)])
    antibiotic_treatment = SelectField("Traitement antibiotique", choices=YES_NO)
    antibiotic_duration = StringField("Durée du traitement ATB en cours", validators=[Optional(), Length(max=80)])
    underlying_chronic_disease = TextAreaField("Maladie chronique sous-jacente", validators=[Optional()])
    main_diagnosis = TextAreaField("Diagnostic principal", validators=[Optional()])
    sampling_date = DateField("Date de prélèvement", validators=[Optional()])
    prescriber_name = StringField("Médecin prescripteur", validators=[DataRequired(), Length(max=160)])
    clinical_context = TextAreaField("Renseignements cliniques complémentaires", validators=[Optional()])
    urgent = BooleanField("Urgent")
    submit = SubmitField("Envoyer au laboratoire")

class SampleForm(FlaskForm):
    sample_number = StringField("N° échantillon", validators=[DataRequired(), Length(max=60)])
    sample_type = SelectField("Type", choices=[("jet_moyen","Jet moyen"),("sonde","Sonde"),("poche","Poche collectrice"),("autre","Autre")])
    sampling_date = DateField("Date prélèvement", validators=[Optional()])
    sampling_time = TimeField("Heure prélèvement", validators=[Optional()])
    reception_date = DateField("Date réception", validators=[Optional()])
    reception_time = TimeField("Heure réception", validators=[Optional()])
    transport_condition = StringField("Transport", validators=[Optional(), Length(max=160)])
    storage_temperature = StringField("Température", validators=[Optional(), Length(max=80)])
    patient_informed = BooleanField("Patient informé des conditions de prélèvement")
    technique_mastered = BooleanField("Technique de prélèvement maîtrisée")
    intimate_toilet = BooleanField("Toilette intime réalisée")
    sterile_container = BooleanField("Flacon stérile utilisé")
    identified_container = BooleanField("Flacon correctement identifié")
    sufficient_volume = BooleanField("Volume d’urines suffisant")
    no_leakage = BooleanField("Absence de fuite / flacon non souillé")
    delay_compliant = BooleanField("Délai miction–réception conforme")
    temperature_compliant = BooleanField("Température / conservation conforme")
    transport_compliant = BooleanField("Conditions de transport conformes")
    sample_nature_compliant = BooleanField("Nature du prélèvement conforme")
    submit = SubmitField("Enregistrer la réception")

class ResultForm(FlaskForm):
    laboratory_name = StringField("Nom du laboratoire sur le bon", validators=[Optional(), Length(max=180)])
    aspect = StringField("Aspect", validators=[Optional(), Length(max=160)])
    leukocytes = StringField("Leucocytes", validators=[Optional(), Length(max=80)])
    red_cells = StringField("Hématies", validators=[Optional(), Length(max=80)])
    epithelial_cells = StringField("Cellules épithéliales", validators=[Optional(), Length(max=160)])
    other_elements = TextAreaField("Autres éléments", validators=[Optional()])
    gram_stain = TextAreaField("Coloration de Gram", validators=[Optional()])
    culture_status = SelectField("Culture", choices=[("positive","Positive"),("negative","Négative"),("contaminated","Contaminée"),("rejected","Rejetée")])
    isolated_germ = StringField("Germe isolé", validators=[Optional(), Length(max=180)])
    culture_details = TextAreaField("Observations culture", validators=[Optional()])
    conclusion = TextAreaField("Conclusion", validators=[Optional()])
    rejection_reason = TextAreaField("Motif de rejet", validators=[Optional()])
    submit = SubmitField("Enregistrer")

class InternalMessageForm(FlaskForm):
    request_number = StringField("N° demande", validators=[Optional(), Length(max=40)])
    recipient_role = SelectField("Destinataire", choices=[("laboratoire", "Laboratoire"), ("prescripteur", "Prescripteur"), ("admin", "Administrateur")])
    subject = StringField("Objet", validators=[DataRequired(), Length(max=180)])
    body = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Envoyer")

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
