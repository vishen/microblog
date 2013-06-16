from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm
from models import User, ROLE_USER, ROLE_ADMIN

@app.route('/')
@app.route('/index')
@login_required
def index():
	user = g.user
	context = {
		'page_title': 'Home',
		'user': user
	}
	return render_template('index.html', **context)


@app.before_request
def before_request():
	g.user = current_user


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
	if g.user is not None and g.user.is_authenticated():
		return redirect(url_for('index'))

	form = LoginForm()
	if form.validate_on_submit():
		session['remember_me'] = form.remember_me.data
		return oid.try_login(form.openid.data, ask_for=('nickname', 'email'))

	context = {
		'page_title': 'Sign In',
		'form': form,
		'providers': app.config['OPENID_PROVIDERS']
	}

	return render_template('login.html', **context)


@oid.after_login
def after_login(response):
	if response.email is None or response.email == '':
		flash('Invalid Login. Please try again.')
		return redirect(url_for('login'))

	user = User.query.filter_by(email=response.email).first()
	if user is None:
		nickname = response.nickname
		if nickname is None or nickname == '':
			nickname = response.email.split('@')[0]

		user = User(nickname=nickname, email=response.email, role=ROLE_USER)
		db.session.add(user)
		db.session.commit()
	
	remember_me = session.pop('remember_me', False)
	login_user(user, remember=remember_me)

	return redirect(request.args.get('next') or url_for('index'))
	


@lm.user_loader
def load_user(id):
	return User.query.get(int(id))
