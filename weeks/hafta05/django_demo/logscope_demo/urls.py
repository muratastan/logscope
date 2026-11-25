from django.urls import path
from events import views
urlpatterns=[
 path('',views.home,name='home'),
 path('catalog/',views.catalog,name='catalog'),
 path('search/',views.search,name='search'),
 path('items/<int:item_id>/',views.item,name='item'),
 path('forms/checkout/',views.checkout,name='checkout'),
 path('auth/login/',views.login,name='login'),
 path('admin/export/',views.rare_export,name='rare_export'),
 path('testing/error/',views.test_error,name='test_error'),
 path('testing/slow/',views.test_slow,name='test_slow'),
]
