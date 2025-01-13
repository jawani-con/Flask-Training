from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app=Flask(__name__)

app.config['SECRET_KEY'] = 'fitness'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"

class Fitness(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(10), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    membership_details = db.relationship('MembershipDetails', backref='user', uselist=False)

class MembershipDetails(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    membership_date = db.Column(db.Date, nullable=False)
    membership_time = db.Column(db.String(10), nullable=False)  # You can use time in string format or Time object
    user_id = db.Column(db.Integer, db.ForeignKey('fitness.id'), nullable=False)

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return Fitness.query.get(int(user_id))

@app.route("/")
def index():
    all_users=Fitness.query.all()
    return render_template("base.html", all_users=all_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']         
        password = request.form['password']
        
        user = Fitness.query.filter_by(username=username).first()
        if user and user.password == password:  
            if user.role.value == 'admin':
                login_user(user)
                return redirect(url_for('admin_home'))
            
            else:
                login_user(user)
                return redirect(url_for('user_home'))
                
        else:
            return "Invalid username or password", 401  
        
    return render_template("login.html")

@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")

@app.route("/user_home")
def user_home():
    return render_template("user_home.html")

@app.route('/all_members', methods=['GET'])
def all_members():
    all_users = Fitness.query.filter_by().all()
    return render_template("all_members.html", all_users=all_users)

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        id = request.form.get('id')  
        username = request.form.get('username')
        password = request.form.get('password')

        if not id or not username or not password:
            return "Missing form data", 

        existing_user = Fitness.query.filter_by(id=id).first()
        if existing_user:
            return f"User with ID {id} already exists!"

        new_user = Fitness(id=id, username=username, password=password, role=UserRole.USER)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("admin_home"))

    return render_template('add_member.html')

# @app.route('/update_member', methods=['GET', 'POST'])
# def update_member():
#     if request.method == 'POST':
#         id = request.form.get('id') 

#         if not id:
#             return "User id required"
        
#         user=Fitness.query.filter_by(id=id).first() 
#         if not user:
#             return f"User with {id} does not exist"
        
#         membership_details=user.membership_details
#         username = request.form.get('username')
#         membership_date = request.form.get('membership_date')
#         membership_time = request.form.get('membership_time')

#         if username:
#             user.username = username

#         if membership_details:
#             if membership_date:
#                 membership_details.membership_date = datetime.strptime(membership_date, "%Y-%m-%d").date()
#             if membership_time:
#                 membership_details.membership_time = membership_time
#         else:
#             new_membership_details = MembershipDetails(
#                 user_id=user.id,
#                 membership_date=datetime.strptime(membership_date, "%Y-%m-%d").date(),
#                 membership_time=membership_time
#             )
#             db.session.add(new_membership_details)

#         db.session.commit()

#         return redirect(url_for("admin_home"))

#     return render_template('update_member.html')

@app.route('/update_member', methods=['GET', 'POST'])
def update_member():
    if request.method == 'POST':
        id = request.form.get('id')

        if not id:
            return "User ID is required!", 400

        user = Fitness.query.filter_by(id=id).first()

        if not user:
            return f"User with ID {id} does not exist!", 404

        if 'username' in request.form:
            username = request.form.get('username')
            membership_date = request.form.get('membership_date')
            membership_time = request.form.get('membership_time')

            if username:
                user.username = username

            membership_details = user.membership_details
            if membership_details:
                if membership_date:
                    membership_details.membership_date = datetime.strptime(membership_date, "%Y-%m-%d").date()
                if membership_time:
                    membership_details.membership_time = membership_time
            else:
                new_membership_details = MembershipDetails(
                    user_id=user.id,
                    membership_date=datetime.strptime(membership_date, "%Y-%m-%d").date() if membership_date else None,
                    membership_time=membership_time
                )
                db.session.add(new_membership_details)

            db.session.commit()
            return redirect(url_for('admin_home'))

        return render_template(
            'update_member_form.html',
            user=user,
            membership_details=user.membership_details
        )

    return render_template('update_member.html')


@app.route('/delete_member', methods=['GET', 'POST'])
def delete_member():
    if request.method == 'POST':
        username = request.form.get('username')

        if not username:
            return "Please provide Username."

        if username:
            user_to_delete = Fitness.query.filter_by(username=username).first()

        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            return f"'{user_to_delete.username}' deleted."

        else:
            return "User not found."

    return render_template('delete_member.html')

@app.route('/view_details', methods=['GET'])
def view_details():
    user = current_user  
    membership_details = user.membership_details

    return render_template('view_details.html', user=user, membership_details=membership_details)

@app.route('/renew_membership', methods=['GET', 'POST'])
def renew_membership():

    if request.method == 'POST':
        print("POST request received for /renew_membership")
        print(f"Form Data: {request.form}")
        membership_date = request.form.get('membership_date')
        membership_time = request.form.get('membership_time')

        if not membership_date or not membership_time:
            return "Membership date and time are required!"

        membership_details = current_user.membership_details
        if not membership_details:
            return "Membership details not found to renew."

        membership_details.membership_date = datetime.strptime(membership_date, "%Y-%m-%d").date()
        membership_details.membership_time = membership_time
        db.session.commit()
 
    return render_template('renew_membership.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  

        Fitness.query.delete()
        MembershipDetails.query.delete()
        db.session.commit()
        new_user1 = Fitness(id=1, username="one", password="abc123", role=UserRole.ADMIN)
        db.session.add(new_user1)

        new_user2 = Fitness(id=2, username="two", password="abc123", role=UserRole.USER)
        db.session.add(new_user2)
        membership_details = MembershipDetails(
            user_id=new_user2.id,  
            membership_date=datetime.strptime("2025-01-01", "%Y-%m-%d").date(),  
            membership_time="1 year"  
        )
        db.session.add(membership_details)

        db.session.commit()

    app.run(debug=True)