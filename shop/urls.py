from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^cart$', views.ShowCartView.as_view(), name='cart'),
    url(r'^checkout$', views.CheckoutView.as_view(), name='checkout'),
    url(r'^confirm$', views.ConfirmView.as_view(), name='confirm'),
    url(r'^execute$', views.ExecuteView.as_view(), name='execute'),
]
