from django.contrib import admin
from .models import Customer, CustomerAccount, CashDeposit, InterBankTransfer, OtherBankTransfer, Notification, \
    Transaction


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number', 'customer_id')
    search_fields = ('full_name', 'email', 'phone_number', 'customer_id')


@admin.register(CustomerAccount)
class CustomerAccountAdmin(admin.ModelAdmin):
    list_display = ('customer', 'account_number', 'account_type', 'kyc_status')
    list_filter = ('account_type', 'kyc_status')
    search_fields = ('account_number', 'customer__full_name')


@admin.register(CashDeposit)
class CashDepositAdmin(admin.ModelAdmin):
    list_display = ('account', 'amount', 'deposit_date')
    list_filter = ('deposit_date',)
    search_fields = ('account__account_number',)


@admin.register(InterBankTransfer)
class InterBankTransferAdmin(admin.ModelAdmin):
    list_display = ('sender_account', 'receiver_account', 'amount', 'transfer_method', 'transfer_date')
    list_filter = ('transfer_method', 'transfer_date')
    search_fields = ('sender_account__account_number', 'receiver_account__account_number')


@admin.register(OtherBankTransfer)
class OtherBankTransferAdmin(admin.ModelAdmin):
    list_display = (
        'sender_account', 'receiver_name', 'receiver_account_number', 'amount', 'transfer_method', 'transfer_date')
    list_filter = ('transfer_method', 'transfer_date')
    search_fields = ('sender_account__account_number', 'receiver_account_number', 'receiver_name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'amount', 'transaction_type', 'transaction_date')
    search_fields = ('sender__account_number', 'receiver__account_number')
    list_filter = ('transaction_type', 'transaction_date')

    def has_add_permission(self, request):
        return False  # Prevent adding transactions

    def has_change_permission(self, request, obj=None):
        return False  # Prevent modifying transactions

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deleting transactions


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'notification_type', 'created_at')
    list_filter = ('notification_type', 'created_at')
    search_fields = ('recipient__full_name', 'message')
