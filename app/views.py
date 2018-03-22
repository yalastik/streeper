# views.py
import datetime
import validators

import stripe
from flask_mail import Message
import regex as re
import requests
from lxml import html

from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_user, login_required, logout_user
from itsdangerous import SignatureExpired
from werkzeug.security import check_password_hash, generate_password_hash

from app.channel_info import ChannelInfo
from app.generator import getrandompassword
from models import User, Channel, Post, Withdrawal
from forms import ChangeMailForm, ChangePasswordForm, ChangeUsernameForm, CreateChannelForm, LoginForm, \
    RegisterForm, ResetForm, CreatePostForm, TopUpBalanceForm, WithdrawalForm

from app import app, login_manager, db, mail, s


# login loading
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# main page
@app.route('/')
def index():
    return render_template("navbar/index.html")


# marketplace page
# @app.route('/marketplace')
# # @login_required
# def marketplace():
#     channels = Channel.query.filter(Channel.confirmed == 1)
#     return render_template("navbar/marketplace.html", channels=channels)


@app.route('/marketplace', methods=['GET', 'POST'])
def marketplace():
    channels = Channel.query.filter(Channel.confirmed == 1)
    if request.method == 'POST':
        category = request.form['sel']
        price = request.form['pf'].split(',')
        subscribers = request.form['sf'].split(',')
        if category.lower() == 'all':
            channels = Channel.query.filter(Channel.price >= price[0]). \
                filter(Channel.price <= price[1]). \
                filter(Channel.subscribers >= subscribers[0]). \
                filter(Channel.subscribers <= subscribers[1]). \
                filter(Channel.confirmed == 1)

            return render_template('navbar/marketplace.html', channels=channels, curr_cat=category, curr_price=price,
                                   curr_subs=subscribers)
        else:
            channels = Channel.query.filter(Channel.price >= price[0]). \
                filter(Channel.price <= price[1]). \
                filter(Channel.subscribers >= subscribers[0]). \
                filter(Channel.subscribers <= subscribers[1]). \
                filter(Channel.category == category.lower()). \
                filter(Channel.confirmed == 1)

            return render_template('navbar/marketplace.html', channels=channels, curr_cat=category, curr_price=price,
                                   curr_subs=subscribers)

    return render_template('navbar/marketplace.html', channels=channels, curr_cat='All', curr_price=[10, 10000],
                           curr_subs=[0, 300000])


# term of service page
@app.route('/tos')
def terms():
    return render_template("footer/tos.html")


# privacy page
@app.route('/privacy')
def privacy():
    return render_template("footer/privacy.html")


# contact page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        subject = request.form['subject']
        email = request.form['email']
        message = request.form['message']

        if not (subject and email and message):
            flash('Empty fields!')
            return redirect('contact')

        msg = Message(subject, sender='ouramazingapp@gmail.com', recipients=["tbago@yandex.ru"])
        msg.body = message + " {}".format(email)
        mail.send(msg)

        flash("Thank you! We will respond to your question as soon as we can.")
        return redirect('/contact')
    return render_template('footer/contact.html')


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('marketplace'))

    form = LoginForm()
    form1 = ResetForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=(form.email.data).lower()).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('marketplace'))

        flash("Invalid email or/and password!")
        return redirect(url_for('login'))

    if form1.validate_on_submit():
        if not db.session.query(User).filter_by(email=form1.email.data.lower()).first():
            flash("User with email you entered not found!")
            return redirect(url_for('login'))
        else:
            new_password = getrandompassword()
            curr = db.session.query(User).filter_by(email=form1.email.data.lower()).first()
            curr.password = generate_password_hash(new_password, method='sha256')
            db.session.commit()

            msg = Message('Password reset', sender='ouramazingapp@gmail.com', recipients=[form1.email.data])
            msg.html = 'Your new password is <b>{}</b>, you can change it in account settings'.format(new_password)
            mail.send(msg)

            flash('Check your email for further instructions.')
            return redirect(url_for('login'))

    return render_template("forms/login.html", form=form, form1=form1)


# register page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('marketplace'))

    form = RegisterForm()
    if form.validate_on_submit():
        if db.session.query(User).filter_by(email=(form.email.data).lower()).first():
            flash("User already exists!")
            return redirect(url_for('signup'))
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        if re.search('[a-zA-Z]', form.name.data):
            new_user = User(name=form.name.data, email=(form.email.data).lower(), password=hashed_password,
                            type=form.type.data)

            db.session.add(new_user)
            db.session.commit()

            # Message sending
            token = s.dumps(form.email.data, salt='email-confirm')
            msg = Message('Confirm Email', sender='ouramazingapp@gmail.com', recipients=[form.email.data])

            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Your link is {}'.format(link)

            mail.send(msg)
            flash("Success! Now you can log in.")
            return redirect(url_for('login'))
        else:
            flash('Invalid username! It must contain at least 1 english letter.')
            return redirect(url_for('signup'))

    return render_template('forms/signup.html', form=form)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    change_username_form = ChangeUsernameForm()
    change_email_form = ChangeMailForm()
    change_password_form = ChangePasswordForm()
    add_funds_form = TopUpBalanceForm()
    withdrawal_form = WithdrawalForm()

    channels = db.session.query(Channel).filter(Channel.admin_id == current_user.id)

    # actions with changing username
    if change_username_form.validate_on_submit():
        if re.search('[a-zA-Z]', change_username_form.name.data):
            current_user.name = change_username_form.name.data
            db.session.commit()
            flash('Successfully updated your username!')
            return redirect(url_for('settings'))
        else:
            flash('Invalid username! It must contain at least 1 english letter.')
            return redirect(url_for('settings'))

    # actions with changing email
    if change_email_form.validate_on_submit():
        if db.session.query(User).filter_by(email=(change_email_form.new_email.data).lower()).first():
            flash("Error! User with the given email already exists! ")
            return redirect(url_for('settings'))

        if check_password_hash(current_user.password, change_email_form.current_password.data):
            curr = db.session.query(User).filter_by(email=(current_user.email).lower()).first()
            curr.email = change_email_form.new_email.data
            # Message sending
            token = s.dumps(change_email_form.new_email.data, salt='email-confirm')
            msg = Message('Confirm Email', sender='ouramazingapp@gmail.com',
                          recipients=[change_email_form.new_email.data])

            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Your link is {}'.format(link)

            mail.send(msg)
            current_user.email_confirmed = 0
            db.session.commit()
            flash("Success! Now you can confirm your new email!")
            return redirect(url_for('settings'))
        else:
            flash("Error! Password does not match! ")
            return redirect(url_for('settings'))

    # actions with withdrawal
    w = Withdrawal.query.filter_by(user_id=current_user.id)
    if withdrawal_form.validate_on_submit():
        if current_user.current_balance < withdrawal_form.amount.data:
            flash('You do not have enough funds!')
            return redirect('/settings')

        reserved_sum = 0
        for channel in current_user.channels:
            for r in channel.requests:
                if r.posted and datetime.datetime.utcnow() < r.post_time:
                    reserved_sum += r.channel.price
        if current_user.current_balance - reserved_sum < withdrawal_form.amount.data:
            diff = float(current_user.current_balance) - float(
                reserved_sum) if current_user.current_balance - reserved_sum > 0 else 0
            flash('You\'ve got only ${} available, the rest is reserved till the end of posting duration!'.
                  format(diff))
            return redirect('/settings')
        else:
            user = db.session.query(User).filter_by(email=current_user.email).first()
            user.current_balance -= withdrawal_form.amount.data
            db.session.commit()

            new_withdrawal = Withdrawal(status="Request sent", amount=withdrawal_form.amount.data,
                                        card=withdrawal_form.card.data,
                                        user_id=current_user.id)
            db.session.add(new_withdrawal)
            db.session.commit()

            msg = Message('Withdrawal request', sender='ouramazingapp@gmail.com', recipients=["tbago@yandex.ru"])
            msg.body = 'User ' + current_user.email + ' wants ' + str(
                withdrawal_form.amount.data) + ' dollars on ' + str(
                withdrawal_form.card.data)
            mail.send(msg)

            flash('Your request was successfully sent!')
            return redirect('/settings')

    # actions with adding funds
    if add_funds_form.validate_on_submit() and request.method == 'POST':
        curr = db.session.query(User).filter_by(email=current_user.email).first()
        if isinstance(add_funds_form.amount.data, int) and add_funds_form.amount.data > 1:
            customer = stripe.Customer.create(email=request.form['stripeEmail'],
                                              source=request.form['stripeToken'])
            charge = stripe.Charge.create(
                customer=customer,
                amount=add_funds_form.amount.data * 100,
                currency='usd',
                description='Posting'
            )

            curr.current_balance = curr.current_balance + add_funds_form.amount.data
            db.session.commit()

            flash('Successfully replenished your balance!')
            return redirect('/settings')
        else:
            flash('Ooops...Something went wrong')
            return redirect('/settings')

    # actions with changing password
    if change_password_form.validate_on_submit():
        if check_password_hash(current_user.password, change_password_form.current_password.data):
            new_hashed_password = generate_password_hash(change_password_form.new_password.data, method='sha256')

            curr = db.session.query(User).filter_by(email=current_user.email).first()
            curr.password = new_hashed_password

            db.session.commit()
            flash('Successfully updated your password!')
            return redirect(url_for('settings'))
        else:
            flash('Current password is wrong!')
            return redirect(url_for('settings'))

    return render_template('profile/settings.html', change_username_form=change_username_form,
                           change_email_form=change_email_form, add_funds_form=add_funds_form,
                           withdrawal_form=withdrawal_form, w=w, change_password_form=change_password_form,
                           channels=channels)


@app.route('/confirm_channel', methods=['POST', 'GET'])
@login_required
def confirm_channel():
    secret = request.args.get('secret')
    channel = db.session.query(Channel).filter(Channel.secret == secret)
    if channel:
        r = requests.get(
            'https://api.telegram.org/bot435931033:AAHtZUDlQ0DeQVUGNIGpTFhcV1u3wXDjKJY/getChat?chat_id=%s'
            % channel[0].link)
        if not r.json()['ok']:
            flash('Something went wrong!')
            return redirect('/settings')
        else:
            response = r.json()['result']['description']
            if secret in response:
                test = db.session.query(Channel).filter_by(secret=secret).first()
                test.confirmed = 1
                db.session.commit()
                flash('Successfully added your channel into our base!')
                return redirect('/marketplace')
            else:
                flash('Could not find the secret key!')
                return redirect('/settings')
    else:
        abort(404)


@app.route('/add_channel', methods=['GET', 'Post'])
@login_required
def add_channel():
    if current_user.type != 'Brand/Agency':
        flash('You cannot add a channel because of your account type!')
        return redirect(url_for('marketplace'))
    form = CreateChannelForm()
    if form.validate_on_submit():
        if db.session.query(Channel).filter_by(link=form.link.data).first():
            flash('Such marketplace already exists!')
            return redirect(url_for('add_channel'))
        try:
            # some magic with api inside ChannelInfo object
            ci = ChannelInfo(form.link.data)
            form.name.data = ci.name
            new_channel = Channel(name=ci.name,
                                  link=ci.chat_id, description=form.description.data,
                                  subscribers=ci.subscribers,
                                  price=form.price.data, secret=getrandompassword(), category=form.category.data,
                                  image=ci.photo, admin_id=current_user.id)

            db.session.add(new_channel)
            db.session.commit()

            flash('Great! Now you can confirm ownership in account settings section!')

            return redirect(url_for('settings'))
        except NameError:
            flash('No such channel found or incorrect link given!')
            return redirect(url_for('add_channel'))

    return render_template('profile/add_channel.html', form=form)


@app.route('/delete_channel', methods=['POST', 'GET'])
@login_required
def delete_channel():
    secret = request.args.get('secret')
    ch = db.session.query(Channel).filter_by(secret=secret).first()
    if current_user.id == ch.admin_id:
        db.session.delete(ch)
        db.session.commit()

        flash('Successfully deleted channel from database!')
        return redirect('/settings')
    else:
        flash('Ooops, something went wrong!')
        return redirect('/settings')


@app.route('/channel/<r>', methods=['GET', 'POST'])
@login_required
def channel(r):
    chan = db.session.query(Channel).filter_by(link='@' + r).first()
    if not chan:
        abort(404)

    create_post_form = CreatePostForm()

    if create_post_form.validate_on_submit():
        if current_user.current_balance < chan.price:
            flash("You do not have enough funds to advertise here!")
            return redirect("/channel/" + r)
        post = Post(content=create_post_form.content.data,
                    link=create_post_form.link.data,
                    comment=create_post_form.comment.data,
                    channel_id=chan.id,
                    user_id=current_user.id)
        db.session.add(post)
        db.session.commit()

        user = db.session.query(User).filter_by(email=current_user.email).first()
        user.current_balance -= chan.price
        db.session.commit()

        flash('Great! Your request successfully sent to "%s"\'s administrator!' % chan.name)
        return redirect(url_for('marketplace'))
    return render_template('channel.html', chan=chan, form=create_post_form)


@app.route('/user/<uniqid>', methods=['GET', 'POST'])
@login_required
def user(uniqid):
    if str(current_user.id) != uniqid:
        abort(404)
    curr = db.session.query(User).filter_by(email=current_user.email).first()
    if curr is None:
        flash('User\'s id ' + uniqid + ' not found.')
        return redirect(url_for('index'))

    return render_template('profile/user.html', user=curr, time_now=datetime.datetime.utcnow())


def check_post(request_post, link):
    r = requests.get(link)
    text = r.text
    tree = html.fromstring(text)
    message = tree.xpath('//meta[@name="twitter:description"]/@content')[0]
    if request_post.link in message and request_post.content in message:
        return True
    else:
        return False


@app.route('/complain', methods=['POST', 'GET'])
@login_required
def complain():
    request_post = db.session.query(Post).filter_by(id=int(request.args.get('post_id'))).first()
    if not request_post.SHARELINK:
        abort(404)
    if request_post.declined == 1 and request_post.confirmed == 1 or request_post.confirmed == 0:
        abort(404)
    if not check_post(request_post=request_post, link=request_post.SHARELINK):
        curr = db.session.query(User).filter_by(email=current_user.email).first()
        curr.current_balance += request_post.channel.price
        admin = db.session.query(User).filter_by(id=request_post.channel.admin.id).first()
        admin.current_balance -= request_post.channel.price
        request_post.declined = 1

        db.session.commit()
        flash('Great! Successful price refund!')
        return redirect('/user/%s' % current_user.id)

    flash('Post is valid, so calm down!')

    return redirect('/user/%s' % current_user.id)


@app.route('/accept_request', methods=['POST', 'GET'])
@login_required
def accept_request():
    request_post = db.session.query(Post).filter_by(id=int(request.args.get('request_id'))).first()
    request_post.confirmed = True
    db.session.commit()
    flash('Great! You now have to confirm your posting via ad post\'s SHARE LINK!')
    return redirect('/user/%s' % current_user.id)


@app.route('/decline_request', methods=['POST', 'GET'])
@login_required
def decline_request():
    request_post = db.session.query(Post).filter_by(id=int(request.args.get('request_id'))).first()
    request_post.declined = 1
    db.session.commit()

    userForCashback = db.session.query(User).filter_by(id=request_post.user_id).first()
    chan = db.session.query(Channel).filter_by(id=request_post.channel_id).first()
    userForCashback.current_balance += chan.price
    db.session.commit()

    flash('Got rid of that one!')
    return redirect('/user/%s' % current_user.id)


@app.route('/rollback', methods=['POST', 'GET'])
@login_required
def rollback():
    request_post = db.session.query(Post).filter_by(id=int(request.args.get('post_id'))).first()
    db.session.delete(request_post)
    db.session.commit()

    userForCashback = db.session.query(User).filter_by(id=request_post.user_id).first()
    chan = db.session.query(Channel).filter_by(id=request_post.channel_id).first()
    userForCashback.current_balance += chan.price
    db.session.commit()

    flash('Great! Successfully canceled your request!')
    return redirect('/user/%s' % current_user.id)


@app.route('/switch_channel', methods=['POST', 'GET'])
@login_required
def switch_channel():
    request_post = db.session.query(Post).filter_by(id=int(request.args.get('post_id'))).first()
    return redirect('/user/%s' % current_user.id)


@app.route('/remove_row', methods=['POST', 'GET'])
@login_required
def remove_row():
    request_post = db.session.query(Post).filter_by(id=int(request.args.get('post_id'))).first()
    db.session.delete(request_post)
    db.session.commit()
    return redirect('/user/%s' % current_user.id)


@app.route('/confirmSHARELINK', methods=['POST', 'GET'])
@login_required
def confirmSHARELINK():
    link = request.form["link"]
    if not link or not validators.url(link):
        flash("Link is not valid!")
        return redirect('/user/%s' % current_user.id)

    curr = db.session.query(User).filter_by(id=current_user.id).first()

    request_post = db.session.query(Post).filter_by(id=int(request.form['request_id'])).first()
    # r = requests.get(link)
    # text = r.text
    # tree = html.fromstring(text)
    # message = tree.xpath('//meta[@name="twitter:description"]/@content')[0]
    if check_post(request_post=request_post, link=link):
        request_post.posted = 1
        request_post.SHARELINK = link
        now_time = datetime.datetime.utcnow()
        delta = datetime.timedelta(days=1)
        request_post.post_time = now_time + delta
        db.session.commit()

        t = db.session.query(Channel).filter_by(id=request_post.channel_id).first()
        curr.current_balance += t.price
        db.session.commit()
        flash("Great! In 24 hours we will check out the post existence and transfer money to your virtual wallet!")

    else:
        flash('Oops... Didn\'t find the post or it differs from the requested one.')

    return redirect('/user/%s' % current_user.id)


# sending confirmation link
@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        curr = db.session.query(User).filter_by(email=email).first()
        curr.email_confirmed = 1
        db.session.commit()
    except SignatureExpired:
        return '<h1>The confirmation link has expired...</h1>'
    return render_template('additional/confirm_email.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# error 404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404
