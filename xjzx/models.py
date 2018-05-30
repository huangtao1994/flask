import pymysql
from datetime import datetime

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

pymysql.install_as_MySQLdb()
db = SQLAlchemy()

'''
一对多把关系字段定义在多的一端
多对多把关系字段定义在任意一端,多对多需要添加一张额外的表来记录两张表的对应关系
'''


class BaseMode(object):
    create_time = db.Column(db.DateTime, default=datetime.now())
    update_time = db.Column(db.DateTime, default=datetime.now())
    is_Delete = db.Column(db.Boolean, default=False)


class NewsCategory(db.Model, BaseMode):
    # 新闻分类
    __tablename__ = 'news_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10))
    news = db.relationship('NewsInfo', backref='category', lazy='dynamic')


class NewsInfo(db.Model, BaseMode):
    # 新闻类
    __tablename__ = 'news_info'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('news_category.id'))
    pic = db.Column(db.String(50))
    title = db.Column(db.String(30))
    summary = db.Column(db.String(200))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.id'))
    click_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    status = db.Column(db.SmallInteger, default=1)
    reason = db.Column(db.String(100), default='')
    comments = db.relationship('NewsComment', backref='news', lazy='dynamic', order_by='NewsComment.id.desc()')


tb_user_follow = db.Table(
    # 用户收藏新闻关系表
    'tb_user_follow',
    db.Column('origin_user_id', db.Integer, db.ForeignKey('user_info.id'), primary_key=True),
    db.Column('follow_user_id', db.Integer, db.ForeignKey('user_info.id'), primary_key=True),

)
tb_user_collect = db.Table(
    # 用户关注用户关系表
    'tb_news_collect',
    db.Column('user_id', db.Integer, db.ForeignKey('user_info.id'), primary_key=True),
    db.Column('news_id', db.Integer, db.ForeignKey('news_info.id'), primary_key=True)

)


class UserInfo(db.Model, BaseMode):
    # 用户表
    __tablename__ = 'user_info'
    id = db.Column(db.Integer, primary_key=True)
    avatar = db.Column(db.String(50), default='user_pic.png')
    nick_name = db.Column(db.String(20))
    signature = db.Column(db.String(200), default='这人啥都没留下')
    mobile = db.Column(db.String(11))
    password_hash = db.Column(db.String(200))
    gender = db.Column(db.Boolean, default=True)
    public_count = db.Column(db.Integer, default=0)
    follow_conut = db.Column(db.Integer, default=0)
    isAdmin = db.Column(db.Boolean, default=False)

    news = db.relationship('NewsInfo', backref='user', lazy='dynamic')
    comments = db.relationship('NewsComment', backref='user', lazy='dynamic')
    news_collect = db.relationship('NewsInfo', secondary=tb_user_collect, lazy='dynamic')
    follow_user = db.relationship(
        # 类中的关系属性与primaryjoin关联
        # 类中的backref属性与secondaryjoin关联
        'UserInfo',
        secondary=tb_user_follow, lazy='dynamic',
        backref=db.backref('follow_by_user', lazy='dynamic'),
        # 在使用user.follow_user时，user.id与关系表中哪个字段判等
        primaryjoin=id == tb_user_follow.c.origin_user_id,
        # 在使用user.follow_by_user时，user.id与关系表中的哪个字段判等
        secondaryjoin=id == tb_user_follow.c.follow_user_id
    )

    # 密码需要加密存储
    @property
    def password(self):
        pass

    @password.setter
    def password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    # 把用户填写的密码加密后与数据库中的密码对比
    def check_pwd(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    @property
    def avatar_url(self):
        return "/static/news/images/" + self.avatar
        # return current_app.config.get('QINIU_URL') + self.avatar


class NewsComment(db.Model, BaseMode):
    # 评论
    __tablename__ = 'news_comment'
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news_info.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.id'))
    like_count = db.Column(db.Integer, default=0)
    comment_id = db.Column(db.Integer, db.ForeignKey('news_comment.id'))
    msg = db.Column(db.String(200))
    comments = db.relationship('NewsComment', lazy='dynamic')
