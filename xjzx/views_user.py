from flask import Blueprint, make_response, request, jsonify
from flask import current_app
from flask import session
from utils.captcha.captcha import captcha
import random
import re
from models import db, UserInfo
from utils.ytx_sdk.ytx_send import sendTemplateSMS

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/image_yzm')
def image_yzm():
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
