from books import views
from django.conf.urls import url

urlpatterns = [
	url(r'^$',views.index,name='index'),
	url(r'^book/(?P<books_id>\d+)/$',views.book_detail,name='detail'),
	url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)/$', views.list, name='list'), # 列表页
	
]
