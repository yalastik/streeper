from wtforms import StringField, PasswordField, BooleanField, validators, SelectField, IntegerField
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Email, Length

# Initialize login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Incorrect email.'), Length(max=50)])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember me')

# Initialize register form
class RegisterForm(FlaskForm):
    name = StringField('Name', [InputRequired(), Length(min=1, max=50)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Incorrect email.'), Length(max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match.')
    ])
    confirm = PasswordField('Confirm Password')
    type = SelectField('Account type',
                       choices=[('Brand/Agency', 'Brand/Agency'), ('Creator/Influencer', 'Creator/Influencer')])
    tos = BooleanField('I agree to <a href="/tos" style = "color: #54C571;">Terms of Service</a>', validators=[validators.DataRequired()])

# Initialize reset form
class ResetForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Incorrect email.'), Length(max=50)])

# Initialize change password form
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current password', validators=[InputRequired()])
    new_password = PasswordField('New password', validators=[InputRequired(),
                                                             validators.EqualTo('new_password_confirm', message='Passwords do not match.')])
    new_password_confirm = PasswordField('Confirm new password', validators=[InputRequired()])

# Initialize change username channel form
class ChangeUsernameForm(FlaskForm):
    name = StringField('Name', [InputRequired(), Length(min=1, max=50)])


# Initialize change username channel form
class ChangeMailForm(FlaskForm):
    current_password = PasswordField('Current password', validators=[InputRequired()])
    new_email = StringField('New email', validators=[InputRequired(), Email(message='Incorrect email.'), Length(max=50)])


# Initialize create channel form
class CreateChannelForm(FlaskForm):
    link = StringField('Channel link', [InputRequired(), Length(min=1, max=50),validators.url])
    name = StringField('Channel name')
    category_choices = [('cars', 'cars'), ('business', 'business'),
                        ('realty', 'realty'), ('medicine and health', 'medicine and health'),
                        ('marketing', 'marketing'), ('work', 'work'),
                        ('travelling', 'travelling'), ('for women', 'for women'),
                        ('sport', 'sport'), ('culture', 'culture'),
                        ('education', 'education'), ('products and services', 'products and services'),
                        ('18+', '18+'), ('design and decor', 'design and decor'),
                        ('games', 'games'), ('entertainment', 'entertainment'),
                        ('media', 'media'), ('science and technology', 'science and technology'),
                        ('culinary', 'culinary'), ('foreign languages', 'foreign languages'),
                        ('motivation and self-education', 'motivation and self-education'),
                        ('music', 'music'), ('cinematography', 'cinematography'),
                        ('top', 'top')]
    category = SelectField('Category', choices=category_choices)
    description = StringField('Channel description', [InputRequired(), Length(max=200)])
    subscribers = IntegerField('Number of subscribers')
    price = IntegerField('Price', validators=[InputRequired()])


# Initialize create post form
class CreatePostForm(FlaskForm):
    link = StringField('Your project\'s link', [Length(min=1, max=50)])
    content = StringField('Advertisement content', [InputRequired()])
    comment = StringField('Leave some comments', [InputRequired()])

# Initialize top up balance form
class TopUpBalanceForm(FlaskForm):
    amount = IntegerField('Amount', validators=[InputRequired()])

# Initialize withdrawal form
class WithdrawalForm(FlaskForm):
    amount = IntegerField('Amount', validators=[InputRequired()])
    card = IntegerField('Card', validators=[InputRequired()])
