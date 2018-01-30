from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from utils.decorators import login_required
from django.http import HttpResponse,JsonResponse
from users.models import Address
from books.models import Books
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from datetime import datetime
from django.conf import settings
import os
import time
# Create your views here.
from django.db import transaction



@login_required

def order_place(request):
	'''显示提交订单页面'''
	books_ids = request.POST.getlist('books_ids')
	
	if not books_ids:
		return redirect(reverse('cart:show'))

	passport_id = request.session.get('passport_id')
	addr = Address.objects.get_all(passport_id=passport_id)


	books_li = []
	total_count = 0
	total_price = 0

	conn = get_redis_connection('default')
	cart_key = 'cart_%d' % passport_id

	for id in books_ids:
		books = Books.objects.get_books_by_id(books_id=id)
		count = conn.hget(cart_key,id)
		books.count = count

		amount = int(count)*books.price
		books.amount = amount
		books_li.append(books)

		total_count += int(count)
		total_price += books.amount
	
	transit_price = 10
	total_pay = total_price + transit_price

	books_ids = ','.join(books_ids)
	print(addr)
	context = {
		'addr': addr,
		'books_li': books_li,
		'total_count': total_count,
		'total_price': total_price,
		'transit_price': transit_price,
		'total_pay': total_pay,
		'books_ids': books_ids,
	}

	return render(request,'order/place_order.html',context)

@transaction.atomic
def order_commit(request):
	if not request.session.has_key('islogin'):
		return JsonResponse({'res':0,'errmsg':'用户未登录'})
	addr_id = request.POST.get('addr_id')
	pay_method = request.POST.get('pay_method')
	books_ids = request.POST.get('books_ids')

	if not all([addr_id,pay_method,books_ids]):
		return JsonResponse({'res':1,'errmsg':'数据不完整'})

	try:
		addr = Address.objects.get(id=addr_id)
	except Exception as e:
		return JsonResponse({'res':2,'errmsg':'地址信息错误'})

	if int(pay_method) not in OrderInfo.PAY_METHODS_ENUM.values():
		return JsonResponse({'res':3,'errmsg':'不支持的支付方式'})

	passport_id = request.session.get('passport_id')
	order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(passport_id)

	transit_price = 10
	total_count = 0
	total_price = 0
	# 创建一个保存点
	sid = transaction.savepoint()

	try:
		order = OrderInfo.objects.create(
					order_id=order_id,
					passport_id=passport_id,
					addr_id=addr_id,
					total_count=total_count,
					total_price=total_price,
					transit_price=transit_price,
					pay_method=pay_method
			)
		books_ids = books_ids.split(',')
		conn = get_redis_connection('default')
		cart_key = 'cart_%d' %passport_id

		for id in books_ids:
			print(type(id))
			books = Books.objects.get_books_by_id(books_id=id)
			if books is None:
				transaction.savepoint_rollback(sid)
				return JsonResponse({'res':4,'errmsg':'商品信息错误'})

			count = conn.hget(cart_key,id)

			if int(count) > books.stock:
				transaction.savepoint_rollback(sid)
				return JsonResponse({'res':5,'errmsg':'商品库存不足'})

			OrderGoods.objects.create(
						order_id=order_id,
						books_id=id,
						count=count,
						price=books.price
				)


			books.sales += int(count)
			books.stock -= int(count)
			books.save()
			 # 累计计算商品的总数目和总额
			total_count += int(count)
			total_price += int(count) * books.price
 		# 更新订单的商品总数目和总金额
		order.total_count = total_count
		order.total_price = total_price
		order.save()
	except Exception as e:
		transaction.savepoint_rollback(sid)
		return JsonResponse({'res':7,'errmsg':'服务器错误'})

	conn.hdel(cart_key,*books_ids)
	transaction.savepoint_commit(sid)
	return JsonResponse({'res':6})

def order_delete(request):
	# 判断用户是否登录
	if not request.session.has_key('islogin'):
		return JsonResponse({'res': 0, 'errmsg': '请先登录'})

	order_id = request.POST.get('order_id')
	passport_id = request.session.get('passport_id')
	OrderInfo.objects.filter(passport_id=passport_id).filter(order_id=order_id).delete()


	return JsonResponse({'res':1})

def order_delall(request):
	# 判断用户是否登录
	if not request.session.has_key('islogin'):
		return JsonResponse({'res': 0, 'errmsg': '请先登录'})
	order_ids = request.POST.get('boxss')
	passport_id = request.session.get('passport_id')
	order_ids = order_ids.split(',')
	print(order_ids)
	print(type(order_ids))
	for order_id in order_ids:
		OrderInfo.objects.filter(passport_id=passport_id).filter(order_id=order_id).delete()

	return JsonResponse({'res':1})
