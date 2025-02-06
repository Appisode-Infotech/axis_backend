from rest_framework.exceptions import ValidationError

from .models import Customer, CustomerAccount, CashDeposit, InterBankTransfer, OtherBankTransfer, Notification

from rest_framework import serializers
from .models import Transaction


class CustomerSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(required=False, allow_null=True)
    pan_document = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Customer
        fields = '__all__'


class CustomerAccountSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = CustomerAccount
        fields = '__all__'

    def validate_customer(self, value):
        if CustomerAccount.objects.filter(customer=value).exists():
            raise ValidationError("This customer already has an account.")
        return value


class CashDepositSerializer(serializers.ModelSerializer):
    account = CustomerAccountSerializer(read_only=True)

    class Meta:
        model = CashDeposit
        fields = '__all__'


class InterBankTransferSerializer(serializers.ModelSerializer):
    sender_account = CustomerAccountSerializer(read_only=True)
    receiver_account = CustomerAccountSerializer(read_only=True)

    class Meta:
        model = InterBankTransfer
        fields = '__all__'


class OtherBankTransferSerializer(serializers.ModelSerializer):
    sender_account = CustomerAccountSerializer(read_only=True)

    class Meta:
        model = OtherBankTransfer
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    recipient = CustomerSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    sender = CustomerAccountSerializer(read_only=True)
    receiver = CustomerAccountSerializer(read_only=True)

    # Add fields for external receiver details
    receiver_name = serializers.SerializerMethodField()
    receiver_account_number = serializers.SerializerMethodField()
    receiver_ifsc_code = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = '__all__'

    def get_receiver_name(self, obj):
        if obj.receiver is None:
            transfer = OtherBankTransfer.objects.filter(
                sender_account=obj.sender,
                amount=obj.amount,
                transaction_date=obj.transaction_date,
                reference_number=obj.reference_number
            ).first()
            return transfer.receiver_name if transfer else None
        return None

    def get_receiver_account_number(self, obj):
        if obj.receiver is None:
            transfer = OtherBankTransfer.objects.filter(
                sender_account=obj.sender,
                amount=obj.amount,
                transaction_date=obj.transaction_date,
                reference_number=obj.reference_number
            ).first()
            return transfer.receiver_account_number if transfer else None
        return None

    def get_receiver_ifsc_code(self, obj):
        if obj.receiver is None:
            transfer = OtherBankTransfer.objects.filter(
                sender_account=obj.sender,
                amount=obj.amount,
                transaction_date=obj.transaction_date,
                reference_number=obj.reference_number
            ).first()
            return transfer.receiver_ifsc_code if transfer else None
        return None
