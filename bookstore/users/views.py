from django.shortcuts import render,redirect
from users.models import Passport,Address
from order.models import OrderInfo,OrderGoods
from books.models import Books
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect,HttpResponse,JsonResponse
from utils.decorators import login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.mail import send_mail
from django.conf import settings
from django_redis import get_redis_connection
from django.http import HttpResponse
import re

# Create your views here.

def register(request):
	return render(request,'users/register.html')


def register_handle(request):
	username = request.POST.get('user_name')
	password = request.POST.get('pwd')
	email = request.POST.get('email')
	
	if not all([username,password,email]):
		return render(request, 'users/register.html', {'errmsg':'参数不能为空!'})

	if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
		return render(request,'users/register.html',{'errmsg':'邮箱格式不正确'})

	p = Passport.objects.filter(username=username)

	if p:
		return render(request, 'users/register.html', {'errmsg': '用户名已存在！'})

	# 进行业务处理:注册，向账户系统中添加账户
	# Passport.objects.create(username=username, password=password, email=email)
	passport = Passport.objects.add_one_passport(username=username, password=password, email=email)

	# 生成激活的token itsdangerous
	serializer = Serializer(settings.SECRET_KEY, 3600)
	token = serializer.dumps({'confirm':passport.id}) # 返回bytes
	token = token.decode()
	
	# 给用户的邮箱发激活邮件
	send_mail('尚硅谷书城用户激活', '', settings.EMAIL_FROM, [email], html_message='<a href="http://127.0.0.1:8888/user/active/%s/">http://127.0.0.1:8888/user/active/</a>' % token)
	
	# 注册完，还是返回注册页。
	return redirect(reverse('books:index'))


def login(request):
	'''显示登录页面'''
	username = request.COOKIES.get('username','')
	checked = ''

	context = {
		'username': username,
		'checked': checked,
	}
	
	return render(request, 'users/login.html', context)

# users/views.py
def login_check(request):
	'''进行用户登录校验'''
	# 1.获取数据
	username = request.POST.get('username')
	password = request.POST.get('password')
	remember = request.POST.get('remember')
	verifycode = request.POST.get('verifycode')
	# 2.数据校验
	if not all([username, password, remember]):
		# 有数据为空
		return JsonResponse({'res': 2})
	if verifycode.upper() != request.session['verifycode']:
		return JsonResponse({'res': 2})

	# 3.进行处理:根据用户名和密码查找账户信息
	passport = Passport.objects.get_one_passport(username=username, password=password)

	if passport:
		# 用户名密码正确
		# 获取session中的url_path
		# if request.session.has_key('url_path'):
		#     next_url = request.session.get('url_path')
		# else:
		#     next_url = reverse('books:index')
		next_url = request.session.get('url_path', reverse('books:index')) # /user/
		jres = JsonResponse({'res': 1, 'next_url': next_url})

		# 判断是否需要记住用户名
		if remember == 'true':
			# 记住用户名
			jres.set_cookie('username', username, max_age=7*24*3600)
		else:
			# 不要记住用户名
			jres.delete_cookie('username')

		# 记住用户的登录状态
		request.session['islogin'] = True
		request.session['username'] = username
		request.session['passport_id'] = passport.id
		return jres
	else:
		# 用户名或密码错误
		return JsonResponse({'res': 0})

def logout(request):
	request.session.flush()
	return HttpResponseRedirect(reverse('books:index'))
@login_required
def user(request):
	passport_id = request.session.get('passport_id')
	addr = Address.objects.get_all(passport_id=passport_id)

		# 获取用户的最近浏览信息
	con = get_redis_connection('default')
	key = 'history_%d' % passport_id
	# 取出用户最近浏览的5个商品的id
	history_li = con.lrange(key, 0, 3)
	# history_li = [21,20,11]
	# print(history_li)
	# 查询数据库,获取用户最近浏览的商品信息
	# books_li = Books.objects.filter(id__in=history_li)
	books_li = []
	for id in history_li:
		books = Books.objects.get_books_by_id(books_id=id)
		books_li.append(books)
	print(addr)
	
	context = {
			'addr': addr,
			'page': 'user',
			'books_li': books_li
	}
	return render(request,'users/user_center_info.html',context)


@login_required
def address(request):
	passport_id = request.session.get('passport_id')

	if request.method == 'GET':
		addr = Address.objects.get_default_address(passport_id=passport_id)
		return render(request,'users/user_center_site.html',{'addr':addr,'page':'address'})
	else:
		recipient_name = request.POST.get('username')
		recipient_addr = request.POST.get('addr')
		zip_code = request.POST.get('zip_code')
		recipient_phone = request.POST.get('phone')

		if not all([recipient_name,recipient_phone,recipient_addr,zip_code]):
			return render(request,'users/user_center_site.html',{'errmsg':'参数不必为空!'})
		Address.objects.add_one_address(
						passport_id=passport_id,
						recipient_phone=recipient_phone,
						recipient_addr=recipient_addr,
						recipient_name=recipient_name,
						zip_code=zip_code
				)
		return redirect(reverse('user:address'))

@login_required
def order(request):
	passport_id = request.session.get('passport_id')

	order_li = OrderInfo.objects.filter(passport_id=passport_id)

	for order in order_li:
		order_id = order.order_id

		order_books_li = OrderGoods.objects.filter(order_id=order_id)
		total_price = 0

		for order_books in order_books_li:
			count = order_books.count
			price = order_books.price
			amount = count*price

			order_books.amount = amount
			total_price += amount

		order.total_price = total_price

		order.order_books_li = order_books_li

	context = {
		'order_li':order_li,
		'order':order,

	}
	return render(request,'users/user_center_order.html',context)


def verifycode(request):
	#引入绘图模块
	from PIL import Image, ImageDraw, ImageFont
	#引入随机函数模块
	import random
	#定义变量，用于画面的背景色、宽、高输入
	bgcolor = (random.randrange(20, 100), random.randrange(20, 100), 255)
	width = 100
	height = 25
	#创建画面对象
	im = Image.new('RGB', (width, height), bgcolor)
	#创建画笔对象
	draw = ImageDraw.Draw(im)
	#调用画笔的point()函数绘制噪点
	for i in range(0, 100):
		xy = (random.randrange(0, width), random.randrange(0, height))
		fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
		draw.point(xy, fill=fill)
	#定义验证码的备选值
	str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
	#随机选取4个值作为验证码
	rand_str = ''
	for i in range(0, 4):
		rand_str += str1[random.randrange(0, len(str1))]
	#构造字体对象
	font = ImageFont.truetype("FreeMono.ttf", 15)
	#构造字体颜色
	fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))
	#绘制4个字
	draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
	draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
	draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
	draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)
	#释放画笔
	del draw
	#存入session，用于做进一步验证
	request.session['verifycode'] = rand_str
	#内存文件操作
	import io
	buf = io.BytesIO()
	#将图片保存在内存中，文件类型为png
	im.save(buf, 'png')
	#将内存中的图片数据返回给客户端，MIME类型为图片png
	return HttpResponse(buf.getvalue(), 'image/png')