from order import views
from django.conf.urls import url

urlpatterns = [
	url(r'^place/$',views.order_place,name='place'),
	url(r'^commit/$',views.order_commit,name='commit'),
	url(r'^del/$',views.order_delete,name='del'),
	url(r'^delall/$',views.order_delall,name='delall'),
]