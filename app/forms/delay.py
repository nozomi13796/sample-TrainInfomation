from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

class EventForm(FlaskForm):
    rid = SelectField("事由", validators=[DataRequired()], coerce=int)
    detail = TextAreaField("件名", validators=[Optional()])
    submit = SubmitField("登録する")

class DelayInfoForm(FlaskForm):
    t_number = IntegerField("列車番号", validators=[DataRequired()])
    alpha = SelectField("番号種別", validators=[DataRequired()])
    delay_minutes = IntegerField("遅延分数", validators=[Optional()])
    is_cancel = BooleanField("運休")
    is_change = BooleanField("経路変更")
    submit = SubmitField("登録する")
