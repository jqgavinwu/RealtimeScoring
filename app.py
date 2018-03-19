import os
from flask import Flask, abort, request, jsonify, g, url_for
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from pandas import DataFrame, Series
from sklearn.externals import joblib
from sklearn.ensemble import GradientBoostingClassifier
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)


os.chdir('/Users/gavin.wu/Python/Project/FPD')
gbm_tuned = joblib.load('fpd_gbm.pkl')

context = ('/Users/gavin.wu/Python/Project/FPD/server.crt', '/Users/gavin.wu/Python/Project/FPD/server.key')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
api = Api(app)
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


class FindZen(Resource):
    @auth.login_required
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('PriBurFPDScrScore', type=float)
            parser.add_argument('PriBurAR12ScrScore', type=float)
            parser.add_argument('PriBurScr9Score', type=float)
            parser.add_argument('eb_fcra_ebureau.score.credit.201406271103', type=float)
            parser.add_argument('eb_nonFcra_ebureau.score.fraud.201508171101', type=float)
            parser.add_argument('eb_nonFcra_ebureau.score.market.201407171105', type=float)
            parser.add_argument('ida_fcra_ACP3.0_score', type=float)
            parser.add_argument('ida_fcra_ACP4.0_score', type=float)
            parser.add_argument('ida_fcra_CAA5.1_score', type=float)
            parser.add_argument('ida_fcra_CAB5.1_score', type=float)
            parser.add_argument('ida_fcra_CAW5.1_score', type=float)
            parser.add_argument('ln_fp_fp_score', type=float)
            parser.add_argument('ln_rv_score_auto', type=float)
            
            args = parser.parse_args()
            
            test = DataFrame({
            'PriBurFPDScrScore': [float(args['PriBurFPDScrScore'])],
            'PriBurAR12ScrScore': [float(args['PriBurAR12ScrScore'])],
            'PriBurScr9Score': [float(args['PriBurScr9Score'])],
            'eb_fcra_ebureau.score.credit.201406271103': [float(args['eb_fcra_ebureau.score.credit.201406271103'])],
            'eb_nonFcra_ebureau.score.fraud.201508171101': [float(args['eb_nonFcra_ebureau.score.fraud.201508171101'])],
            'eb_nonFcra_ebureau.score.market.201407171105': [float(args['eb_nonFcra_ebureau.score.market.201407171105'])],
            'ida_fcra_ACP3.0_score': [float(args['ida_fcra_ACP3.0_score'])],
            'ida_fcra_ACP4.0_score': [float(args['ida_fcra_ACP4.0_score'])],
            'ida_fcra_CAA5.1_score': [float(args['ida_fcra_CAA5.1_score'])],
            'ida_fcra_CAB5.1_score': [float(args['ida_fcra_CAB5.1_score'])],
            'ida_fcra_CAW5.1_score': [float(args['ida_fcra_CAW5.1_score'])],
            'ln_fp_fp_score': [float(args['ln_fp_fp_score'])],
            'ln_rv_score_auto': [float(args['ln_rv_score_auto'])]})
            
            gbm_prob = gbm_tuned.predict_proba(test)[:,1]
            print(gbm_prob)
            return gbm_prob[0]
        except Exception as e:
            return {'error': str(e)}

api.add_resource(FindZen, '/FindZen')

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(ssl_context=context, debug=True)