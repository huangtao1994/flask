from flask import Blueprint, make_response, request, jsonify, render_template, redirect
from flask import current_app
from flask import session
from utils.captcha.captcha import captcha
import random
import re
from models import db, UserInfo
from utils.ytx_sdk.ytx_send import sendTemplateSMS
import functools
from utils.qiniu_xjzx import upload_pic

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/image_yzm')
def image_yzm():
    # captcha.generate_captcha()为第三方包utils.captcha中的方法
    name, yzm, image = captcha.generate_captcha()
    # yzm表示随机生成的验证码字符串
    # 将数据进行保存，方便方面对比
    session['image_yzm'] = yzm
    # image表示图片的二进制数据
    response = make_response(image)
    # 默认浏览器将数据作为text/html解析
    # 需要告诉浏览器当前数据的类型为image/png
    response.mimetype = 'image/png'
    return response


@user_blueprint.route('/sms_yzm')
def sms_yzm():
    # 接收数据：手机号，图片验证码
    dict1 = request.args  # 从main.js中的get请求获取键
    # print(dict1)
    mobile = dict1.get('mobile')
    yzm = dict1.get('yzm')

    # 对比图片验证码
    if yzm != session['image_yzm']:
        return jsonify(result=1)

    # 随机生成一个4位的验证码
    yzm2 = random.randint(1000, 9999)

    # 将短信验证码进行保存，用于验证
    session['sms_yzm'] = yzm2

    # 发送短信
    # sendTemplateSMS(mobile,{yzm2,5},1)
    print(yzm2)

    return jsonify(result=2)


@user_blueprint.route('/register', methods=['POST'])
def register():
    # 用户名注册
    # 接收页面表单数据
    dict1 = request.form
    mobile = dict1.get('mobile')
    pwd = dict1.get('pwd')
    yzm_image = dict1.get('yzm_image')
    yzm_sms = dict1.get('yzm_sms')

    # 验证数据的有效性

    if not all([mobile, pwd, yzm_image, yzm_sms]):
        return jsonify(result=1)
    if not yzm_image == session['image_yzm']:
        return jsonify(result=2)
    if not int(yzm_sms) == session['sms_yzm']:
        return jsonify(result=3)
    if not re.match(r'([a-zA-Z0-9_]{6,20})', pwd):
        return jsonify(result=4)
    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    # 验证手机号是否存在(用户名是否存在)
    if mobile_count > 0:
        return jsonify(result=5)

    # 验证全部通过,则向数据库写入该账户
    user = UserInfo()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = pwd

    try:
        db.session.add(user)
        db.session.commit()
    except:
        current_app.logger_xjzx.error("用户注册访问数据库失败")
        return jsonify(result=7)
    return jsonify(result=6)


@user_blueprint.route('/login', methods=['POST'])
def login():
    # 登录
    dict1 = request.form
    mobile = dict1.get('mobile')
    pwd = dict1.get('pwd')

    if not all([mobile, pwd]):
        return jsonify(result=1)
    user = UserInfo.query.filter_by(mobile=mobile).first()  # UserInfo.query.filter_by此方法返回的是一个列表,用first取出第一个值

    if user:
        if user.check_pwd(pwd):
            # 状态保持
            session['user_id'] = user.id
            return jsonify(result=2, avatar=user.avatar, nick_name=user.nick_name)
        else:
            # 密码错位
            return jsonify(result=3)
    else:
        # 账号不存在
        return jsonify(result=4)


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    # 退出登录
    del session['user_id']
    return jsonify(result=1)


def login_required(view_fun):
    @functools.wraps(view_fun)
    def fun2(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        return view_fun(*args, **kwargs)

    return fun2


@user_blueprint.route('/')
@login_required
def index():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    return render_template('news/user.html', user=user)


@user_blueprint.route('/base', methods=['GET', 'POST'])
@login_required
def base():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    if request.method == 'GET':
        return render_template('news/user_base_info.html', user=user)
    elif request.method == 'POST':
        # 接收数据
        dict1 = request.form
        nick_name = dict1.get('nick_name')
        signature = dict1.get('signature')
        gender = dict1.get('gender')
        print(nick_name)
        # 查询数据为属性赋值
        user.nick_name = nick_name
        user.signature = signature
        user.gender = bool(gender)
        # 提交到数据库
        db.session.commit()
        return jsonify(result=1)


@user_blueprint.route('/pic',methods=['GET','POST'])
@login_required
def pic():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    if request.method == 'GET':
        return render_template('news/user_pic_info.html',user=user)
    elif request.method == 'POST':
        # 接收文件
        avatar = request.files.get('avatar')
        # 上传到七牛云,并返回文件名
        filename = upload_pic(avatar)
        # 修改用户的头像属性
        user.avatar = filename
        # 提交到数据库
        db.session.commit()

        # 返回响应
        return jsonify(result=1)


@user_blueprint.route('/follow')
@login_required
def follow():
    return render_template('news/user_follow.html')


@user_blueprint.route('/pwd')
@login_required
def pwd():
    return render_template('news/user_pass_info.html')


@user_blueprint.route('/collect')
@login_required
def collect():
    return render_template('news/user_collection.html')


@user_blueprint.route('/release')
@login_required
def release():
    return render_template('news/user_news_release.html')


@user_blueprint.route('/news_list')
@login_required
def news_list():
    return render_template('news/user_news_list.html')
