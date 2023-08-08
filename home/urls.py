from django.urls import path
from . import views


app_name = 'home'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('Bucket/', views.BucketHome.as_view(), name='bucket_home'),
    path('delete_obj_bucket/<str:key>', views.DeleteBucketObject.as_view(), name='delete_obj_bucket'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
