from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^cart$', views.ShowCartView.as_view(), name='cart'),
    url(r'^create-payment$', views.CreatePaymentView.as_view(), name='create-payment'),
    url(r'^execute-payment$', views.ExecutePaymentView.as_view(), name='execute-payment'),
]
