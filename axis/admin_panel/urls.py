from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from . import views
from .views import LoginAPIView, GenerateOTPAPIView, TransactionViewSet, UserTransactionsAPIView, \
    CustomerNotificationsAPIView, GetAccountDetailsView, GetAccountDetailsByAccountNumberView, HandlePaymentAPIView

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet)
router.register(r'accounts', views.CustomerAccountViewSet)
router.register(r'cash-deposits', views.CashDepositViewSet)
router.register(r'interbank-transfers', views.InterBankTransferViewSet)
router.register(r'otherbank-transfers', views.OtherBankTransferViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')

schema_view = get_schema_view(
    openapi.Info(
        title="Banking API",
        default_version='v1',
        description="APIs for Banking Application",
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/login/', LoginAPIView.as_view(), name='login'),
    path('api/generate-otp/', GenerateOTPAPIView.as_view(), name='generate-otp'),
    path('api/homeApi/<str:customer_id>/', UserTransactionsAPIView.as_view(), name='home-api'),
    path('api/notification/<str:customer_id>/', CustomerNotificationsAPIView.as_view(), name='customer-notifications'),
    path('api/customer_account/<str:phone_number>/', GetAccountDetailsView.as_view(), name='get_account_details'),
    path('api/account_details/<str:account_number>/', GetAccountDetailsByAccountNumberView.as_view(),name='get_account_details_by_account_number'),
    path('api/handle-payment/', HandlePaymentAPIView.as_view(), name='handle-payment'),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
