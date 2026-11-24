from django.urls import path
from . import views

app_name = 'workorders'

urlpatterns = [
    path('', views.work_order_list, name='work_order_list'),
    path('create/', views.work_order_create, name='work_order_create'),
    path('<int:pk>/', views.work_order_detail, name='work_order_detail'),
    path('<int:pk>/edit/', views.work_order_edit, name='work_order_edit'),
    path('<int:pk>/close/', views.work_order_close, name='work_order_close'),
    path('<int:work_order_pk>/consumption/create/', views.daily_consumption_create, name='daily_consumption_create'),
    path('<int:work_order_pk>/labor/create/', views.daily_labor_create, name='daily_labor_create'),
]