#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

# ========== SESSION ==========

class ClearSession(Resource):
    def delete(self):
        session['page_views'] = None
        session['user_id'] = None
        return {}, 204

# ========== ARTICLES ==========

class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):
    def get(self, id):
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:
            article = Article.query.filter(Article.id == id).first()
            article_json = jsonify(article.to_dict())
            return make_response(article_json, 200)

        return {'message': 'Maximum pageview limit reached'}, 401

# ✅ NEW: MembersOnlyArticles route
class MembersOnlyArticles(Resource):
    def get(self):
        if not session.get('user_id'):
            return {"error": "Unauthorized"}, 401

        articles = Article.query.filter_by(is_member_only=True).all()
        return [article.to_dict() for article in articles], 200

class MemberOnlyArticleDetail(Resource):
    def get(self, id):
        if not session.get('user_id'):
            return {"error": "Unauthorized"}, 401

        article = db.session.get(Article, id)
        if article and article.is_member_only:
            return article.to_dict(), 200
        return {"error": "Article not found or not member-only"}, 404

# ========== AUTH ==========

class Login(Resource):
    def post(self):
        username = request.get_json()['username']
        user = User.query.filter(User.username == username).first()
        session['user_id'] = user.id
        return user.to_dict(), 200

class Logout(Resource):
    def delete(self):
        session['user_id'] = None
        return {}, 204

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return user.to_dict(), 200
        return {}, 401

# ========== ROUTES ==========

api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(MembersOnlyArticles, '/members_only_articles')
api.add_resource(MemberOnlyArticleDetail, '/members_only_articles/<int:id>')

# ========== RUN ==========

if __name__ == '__main__':
    app.run(port=5555, debug=True)
