import os
import json
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://iic3103_t0_postgresql_t3v4_user:50ZSz6J3ybXYPED9L8Uzi9jJ77yL7M3f@dpg-co7k9hcf7o1s738ibi80-a.oregon-postgres.render.com/iic3103_t0_postgresql_t3v4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, support_credentials=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique = True, nullable = False)
    avatar = db.Column(db.String(100), nullable = False)
    created = db.Column(db.DateTime, default = datetime.now)

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'avatar': self.avatar,
            'created': self.created.strftime('%Y-%m-%d %H:%M:%S')
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable = False)
    content = db.Column(db.String(100), nullable = False)
    image = db.Column(db.String(100), nullable = False)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    user = db.relationship('User', backref = db.backref('posts', lazy = True))
    created = db.Column(db.DateTime, default = datetime.now)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image': self.image,
            'userId': self.userId,
            'created': self.created.strftime('%Y-%m-%d %H:%M:%S')
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.String(100), nullable = False)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    user = db.relationship('User', backref = db.backref('comments', lazy = True))
    postId = db.Column(db.Integer, db.ForeignKey('post.id'), nullable = False)
    post = db.relationship('Post', backref = db.backref('comments', lazy = True))
    created = db.Column(db.DateTime, default = datetime.now)

    def serialize(self):
        return {
            'id': self.id,
            'content': self.content,
            'userId': self.userId,
            'postId': self.postId,
            'created': self.created.strftime('%Y-%m-%d %H:%M:%S')
        }

@app.route('/')
def index():
    users = User.query.all()
    posts = Post.query.all()
    return render_template('index.html', users = users, posts = posts)

@app.route('/users', methods = ['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200

@app.route('/users/<int:user_id>', methods=['GET'])
def get_one_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify(user.serialize()), 200
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/users/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    user = User.query.get(user_id)
    if user:
        posts = user.posts
        return jsonify([post.serialize() for post in posts]), 200
    else:
        return jsonify({'error': 'User not found'}), 404
    
@app.route('/users', methods=['POST'])
def create_user():
    print(request)
    data = request.json
    if 'username' not in data:
        return jsonify({'error': 'missing parameter: username'}), 400
    if 'avatar' not in data:
        return jsonify({'error': 'missing parameter: avatar'}), 400
    
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409  # 409 Conflict
        
    new_user = User(username=data['username'], avatar=data['avatar'])
    db.session.add(new_user)
    db.session.commit()
    user_json = {
        'id': new_user.id,
        'username': new_user.username,
        'avatar': new_user.avatar,
        'created': new_user.created.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    ordered_json = json.dumps(user_json, sort_keys=False)
    
    return ordered_json, 201
    
@app.route('/posts', methods = ['GET'])
def get_posts():
    posts = Post.query.all()
    return jsonify([post.serialize() for post in posts]), 200

@app.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    post = User.query.get(post_id)
    if post:
        comments = post.comments
        return jsonify([comment.serialize() for comment in comments]), 200
    else:
        return jsonify({'error': 'Post not found'}), 404
    
@app.route('/posts', methods=['POST'])
def create_post():
    data = request.json
    user_id = data.get('userId')
    user = User.query.get(user_id)
    if user is None:
        error_message = {"error": f"User with id {user_id} does not exist"}
        return jsonify(error_message), 404
    new_post = Post(title=data['title'], content=data['content'], 
                    image=data['image'], userId=data['userId'])
    db.session.add(new_post)
    db.session.commit()
    post_json = {
            'id': new_post.id,
            'title': new_post.title,
            'content': new_post.content,
            'image': new_post.image,
            'userId': new_post.userId,
            'created': new_post.created.strftime('%Y-%m-%d %H:%M:%S')
    }
    ordered_json = json.dumps(post_json, sort_keys=False)
    
    return ordered_json, 201

@app.route('/comments', methods = ['GET'])
def get_comments():
    comments = Comment.query.all()
    return jsonify([comment.serialize() for comment in comments]), 200

@app.route('/comments', methods=['POST'])
def create_comment():
    data = request.json
    if 'content' not in data:
        error_message = {"error": "missing parameter: content"}
        return jsonify(error_message), 400
    user_id = int(data.get('userId'))
    user = User.query.get(user_id)
    if user is None:
        error_message = {"error": f"user with id {user_id} not found"}
        return jsonify(error_message), 404
    post_id = data.get('postId')
    post = Post.query.get(post_id)
    if post is None:
        error_message = {"error": f"post with id {post_id} not found"}
        return jsonify(error_message), 404
    new_comment = Comment(content=data['content'], userId=data['userId'],
                       postId = data['postId'])
    db.session.add(new_comment)
    db.session.commit()
    comment_json = {
            'id': new_comment.id,
            'content': new_comment.content,
            'userId': new_comment.userId,
            'postId': new_comment.postId,
            'created': new_comment.created.strftime('%Y-%m-%d %H:%M:%S')
        }
    ordered_json = json.dumps(comment_json, sort_keys=False)
    
    return ordered_json, 201

@app.route('/reset', methods=['POST'])
def delete_all_data():
    if request.method == 'POST':
        db.session.close()

        # Elimina todas las tablas de la base de datos
        db.reflect()
        db.drop_all()

        # Vuelve a crear las tablas
        db.create_all()
        return jsonify({}), 200
    else:
        return jsonify({'error': 'Método no permitido'}), 405
    
@app.route('/populate', methods=['POST'])
def load_data():
    file_path = 'data.json'

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            users = data.get('users', [])
            posts = data.get('posts', [])
            comments = data.get('comments', [])

            for user_data in users:
                existing_user = User.query.filter_by(username=user_data['username']).first()
                if not existing_user:
                    new_user = User(username=user_data['username'], avatar=user_data['avatar'])
                    db.session.add(new_user)

            for post_data in posts:
                new_post = Post(title=post_data['title'], content=post_data['content'], 
                                image=post_data['image'], userId=post_data['userId'])
                db.session.add(new_post)

            for comment_data in comments:
                new_comment = Comment(content=comment_data['content'], userId=comment_data['userId'],
                                    postId=comment_data['postId'])
                db.session.add(new_comment)

            db.session.commit()
            return jsonify({}), 200
    else:
        return jsonify({'error': 'El archivo no existe'}), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug = True, port = 10000, host="0.0.0.0")