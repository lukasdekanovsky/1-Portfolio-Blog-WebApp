from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField,TextAreaField, SubmitField, IntegerField, URLField, FloatField, validators
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

class AddProject(FlaskForm):
    intro_title = StringField(label="Enter the main project title", validators=[validators.DataRequired()])
    title = StringField(label="Project subtitle", validators=[validators.DataRequired()])
    version = StringField(label="Project version", validators=[validators.DataRequired()])
    technologies = StringField(label="Which key technologies are in this project?", validators=[validators.DataRequired()])
    description = StringField(label="Project description", validators=[validators.DataRequired()])
    image = FileField(label="Upload project image")
    gitlink = URLField(label="Enter github repo link", validators=[validators.DataRequired()])
    submit = SubmitField(label="Submit new project")

class EditProject(FlaskForm):
    new_intro_title = StringField(label="Enter the main project title")
    new_title = StringField(label="Project subtitle")
    new_version = StringField(label="Project version")
    new_technologies = StringField(label="Which key technologies are in this project?")
    new_description = StringField(label="Project description")
    new_image = FileField(label="Upload project image")
    new_gitlink = URLField(label="Enter github repo link")
    submit = SubmitField(label="Submit changes")


# ----------------------------------------------------------------------------------------------------------

class RegisterForm(FlaskForm):
    email = StringField(label="Email", validators=[validators.DataRequired()])
    password = StringField(label="Password", validators=[validators.DataRequired()])
    name = StringField(label="Name", validators=[validators.DataRequired()])
    submit = SubmitField(label="Sign me up!")

class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[validators.DataRequired()])
    password = StringField(label="Password", validators=[validators.DataRequired()])
    submit = SubmitField(label="Log in!")

class CreatePostForm(FlaskForm):
    title = StringField(label="Title", validators=[validators.data_required()])
    subtitle = StringField(label="Subtitle", validators=[validators.DataRequired()])
    img_url = StringField(label="Image URL", validators=[validators.DataRequired(), validators.URL()])
    body = TextAreaField(label="Blog main body", validators=[validators.DataRequired()])
    submit = SubmitField(label="Submit your post")

class CommentForm(FlaskForm):
    comment_text = TextAreaField("", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")