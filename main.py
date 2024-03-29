from flask import Flask, abort, render_template, redirect, url_for, request, session, send_from_directory, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, LargeBinary, Text
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from wtforms import StringField, SubmitField, IntegerField, URLField, FloatField, validators
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from functools import wraps
import requests
import os
import psycopg2
from datetime import date

from form import AddProject, EditProject, RegisterForm, LoginForm, CreatePostForm, CommentForm


app = Flask(__name__)
#app.secret_key = "238JRjhgasdadasdask097kdKTTR5532948UJDZhhduzeůí9?"
#app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b' # OFF for deploy
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")   #ON for deploy
app.config["UPLOAD_PATH"] = "../static/images/project_images"
ckeditor = CKEditor(app)
Bootstrap5(app)

# ------------- FLASK-LOGIN ----------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# ----- ADDING PROFILE IMAGES TO THE PROFILE SECTION ---------------
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)



# ---------- DATABASE CREATION -------------------------------------
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///personal-webpage.db")  #ON
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///personal-webpage.db" # OFF for deploy
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


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    # Parent relationship to the comments
    comments = relationship("Comment", back_populates="parent_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    # This will act like a list of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    # Parent relationship: "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Child relationship:"users.id" The users refers to the tablename of the User class.
    # "comments" refers to the comments property in the User class.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    # Child Relationship to the BlogPosts
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")



with app.app_context():
    db.create_all()

# -----------------------------PORTFOLIO URL ------------------------------------
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

# -----------------------------BLOG URL ------------------------------------
#### ADMIN DECORATOR #####
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # abort process and return 403 error if user is not admin
        if current_user.id != 1:
            return abort(403)
        # if user id = 1 == admin, continue the function
        return f(*args, **kwargs)
    
    return decorated_function

#### MAIN BLOG PAGE #####
@app.route("/blog")
def blog():
    # READ all Blog posts from database
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("blog.html", blog_posts = posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        # TODO 1) Check if user emain is not already present in the database
        result = db.session.execute(db.select(User).where(User.email == register_form.email.data))
        user = result.scalar()

        if user:
            # User already exists
            flash("This email is already used")
            return redirect(url_for("login"))

        # TODO 2) new user -> HASHING and SOLTING of the password
        hash_and_salted_password = generate_password_hash(
            register_form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        # TODO 3) adding New User to the DB
        new_user = User(
            email=register_form.email.data,
            name=register_form.name.data,
            password=hash_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        # TODO 4) authentication of the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("blog"))

    else:
        return render_template("register.html", form=register_form, current_user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        password = login_form.password.data
        email = login_form.email.data

        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        # TODO 1) There is no such user with this email:
        if not user:
            flash("This email does not exist, please try to log in again.")
            print("LOG IN NOT SUCCESFULL")
            return redirect(url_for("login"))
        
        # TODO 2) The password inserted is not correct:
        elif not check_password_hash(user.password, password):
            flash("Wrong password, please try again.")
            print("LOG IN NOT SUCCESFULL")
            return redirect(url_for("login"))
        
        # TODO 3) Email and Password correct and in database
        else:
            login_user(user)
            print("LOG IN SUCCESFULL")
            return redirect(url_for("blog"))
        
    return render_template("login.html", form = login_form, current_user=current_user)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("blog"))

@app.route("/new-post", methods= ["GET", "POST"])
@admin_only
def add_post():
    post_form = CreatePostForm()
    if post_form.validate_on_submit():
        new_post = BlogPost(
            title = post_form.title.data,
            subtitle = post_form.subtitle.data,
            body = post_form.body.data,
            img_url = post_form.img_url.data,
            author = current_user,
            date = date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("blog"))
    else:
        return render_template("add_post.html", form = post_form, current_user=current_user)

@app.route("/read/<int:post_id>", methods=["GET", "POST"])
def read_post(post_id):
    post_to_read = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        # only authenticated users can read and comment
        if not current_user.is_authenticated:
            flash("You first need to login or register to comment.")
            return redirect(url_for("login"))
        
        new_comment = Comment(
            text = comment_form.comment_text.data,
            comment_author = current_user,
            parent_post = post_to_read
            # author_id=current_user.id,
            # post_id=post_id
        )

        db.session.add(new_comment)
        db.session.commit()
        comment_form.comment_text.data = ""
        return redirect(url_for("read_post", post_id=post_id))
    
    return render_template("read_coment_post.html", post=post_to_read, current_user=current_user, form=comment_form)

@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post_to_edit = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post_to_edit.title,
        subtitle=post_to_edit.subtitle,
        img_url=post_to_edit.img_url,
        author=post_to_edit.author,
        body=post_to_edit.body
    )
    if edit_form.validate_on_submit():
        post_to_edit.title = edit_form.title.data
        post_to_edit.subtitle = edit_form.subtitle.data
        post_to_edit.img_url = edit_form.img_url.data
        post_to_edit.author = current_user
        post_to_edit.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("read_post", post_id=post_to_edit.id))
    return render_template("add_post.html", form = edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("blog"))

@app.route("/delete_comment/<int:comment_id>/<int:post_id>")
@admin_only
def delete_comment(comment_id, post_id):
    comment_to_delete = db.get_or_404(Comment, comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for("read_post", post_id = post_id))



if __name__ == "__main__":
    app.run(debug=False)