from flask import Flask, render_template, redirect, url_for, request, session, send_from_directory
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, LargeBinary
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, IntegerField, URLField, FloatField, validators
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import requests
import os


app = Flask(__name__)
app.secret_key = "238JRjhgdg838#sk097kdKTTR5532948UJDZhhduzeůí9?"
app.config["UPLOAD_PATH"] = "../static/images/project_images"

# ---------- DATABASE CREATION -------------------------------------
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-books-collection.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# ----------DATABASE TABLE CREATION ----------------------------------------
class Project(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intro_title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    technologies: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    gitlink: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'

with app.app_context():
    db.create_all()

# ------------- FORMS ---------------------------------------------------
# 1) Add new project form
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



# ----------------------------- URL ------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/portfolio")
def portfolio():
    # READ all the projects from db and show them in corresponding cards
    database = db.session.execute(db.select(Project).order_by(Project.id))
    all_projects = database.scalars().all() # -> we have a list of projects
    db.session.commit()
    return render_template("portfolio.html", projects = all_projects)


@app.route("/portfolio/add", methods =["GET", "POST"])
def add_portfolio():
    project_form = AddProject()
    
    if project_form.validate_on_submit(): # == POSTED
        # IMAGE save from form to the path
        filename = secure_filename(project_form.image.data.filename)
        project_form.image.data.save('./static/images/project_images/' + filename)
        # CREATE a NEW PROJECT DB RECORD
        new_project = Project(intro_title=project_form.intro_title.data,
                            title = project_form.title.data,
                            version = project_form.version.data,
                            technologies = project_form.technologies.data,
                            description = project_form.description.data,
                            image = filename,
                            gitlink = project_form.gitlink.data)
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for("portfolio"))
    else:
        return render_template("add.html", form_project = project_form)

@app.route("/portfolio/edit", methods=["GET", "POST"])
def edit_portfolio():
    edit_form = EditProject()

    if edit_form.validate_on_submit():
         # CHANGE SELECTED RECORD
        project_id = request.form["id"]
        project_to_edit = db.session.execute(db.select(Project).where(Project.id == project_id)).scalar()

        # ------------------DATA FROM FORM---------------------------------
        new_intro_title = edit_form.new_intro_title.data
        new_title = edit_form.new_title.data
        new_version = edit_form.new_version.data
        new_technologies = edit_form.new_technologies.data

        if edit_form.new_image.data != None:
            new_filename = secure_filename(edit_form.new_image.data.filename)
            edit_form.new_image.data.save('./static/images/project_images/' + new_filename)
        
        new_description = edit_form.new_description.data
        new_gitlink = edit_form.new_gitlink.data
        print(new_title)
        # --------------------DATA UPDATE-----------------------

        if new_intro_title:
            project_to_edit.intro_title = new_intro_title
        if new_title:
            project_to_edit.title = new_title
        if new_version:
            project_to_edit.version = new_version
        if new_technologies:
            project_to_edit.technologies = new_technologies
        if new_description:
            project_to_edit.description = new_description
        if edit_form.new_image.data:
            project_to_edit.image = new_filename
        if new_gitlink:
            project_to_edit.gitlink = new_gitlink
       
        db.session.commit()
        return redirect(url_for("portfolio"))
        
    
    # Read current project data selected 
    project_id = request.args.get("id")
    selected_project = db.session.execute(db.select(Project).where(Project.id == project_id)).scalar()

    return render_template("edit.html", project = selected_project, form = edit_form)


@app.route("/portfolio/delete", methods = ["GET"])
def delete_portfolio():
    project_id = request.args.get("id")
    project_to_delete = db.get_or_404(Project, project_id)
    db.session.delete(project_to_delete)
    db.session.commit()
    return redirect(url_for("portfolio"))   

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)