from flask import Flask, render_template,redirect,request,flash, url_for
from flask_login import LoginManager, UserMixin,login_user,login_required,logout_user,current_user
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os 
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskManagerDB.db"
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False
db=SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class MyTask(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100),nullable=False)
    content=db.Column(db.String(500),nullable=False)
    completed=db.Column(db.Integer,default=0)
    created=db.Column(db.DateTime,default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

    def __str__(self):
        return f"Task {self.id}"
    
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(200), unique=True,nullable=False)
    email = db.Column(db.String(200),unique=True,nullable=False)
    password = db.Column(db.String(200),nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
with app.app_context():
    db.create_all()

  
@app.route('/register/',methods=['GET','POST'])
def register():
    if request.method =='POST':
        username=request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email,password=hashed_password)


        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! You can now log in. ","success")
            return redirect(url_for('login'))
        
        except Exception as e:
            return f'Error: {e}'
    return render_template('register.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Login failed. Invalid login credentials",'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/',methods=["POST","GET"])
@login_required
def index():
    if request.method=='POST':
        current_task = request.form['content']
        current_task_title = request.form['title']
        new_task = MyTask(content=current_task, title=current_task_title,user_id=current_user.id)
        
        try:
            db.session.add(new_task)
          
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return f"Error: {e}"
    else:
        tasks = MyTask.query.filter_by(user_id=current_user.id).order_by(MyTask.created).all()
        return render_template('index.html',tasks=tasks)


@app.route('/delete/<int:id>')
@login_required
def delete(id:int):
    delete_task = MyTask.query.get_or_404(id)
    if delete_task.user_id != current_user.id:
        flash("You don not have permission to delete this task",'danger')
        return redirect(url_for('index'))
    try:
        db.session.delete(delete_task)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f"Error: {e}"

@app.route('/update/<int:id>',methods=['GET','POST'])
@login_required
def update(id:int):
    task = MyTask.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash("You don not have permission to update this task",'danger')
        return redirect(url_for('index'))
    if request.method =='POST':
        task.content = request.form['content']
        task.title = request.form['title']
        try:
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f"Error: {e}"
    else:
        return render_template('update.html',task=task)












if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)