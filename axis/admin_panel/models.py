import uuid

from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
import datetime
from django.core.mail import send_mail


# CUSTOMERS
def validate_dob(value):
    today = datetime.date.today()
    min_age_date = today - datetime.timedelta(days=18 * 365.25)  # Account for leap years
    if value > min_age_date:
        raise ValidationError("You must be at least 18 years old.")


class Customer(models.Model):
    full_name = models.CharField(max_length=255)
    dob = models.DateField(validators=[validate_dob])
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=10,
        validators=[MinLengthValidator(10), MaxLengthValidator(10),
                    RegexValidator(r'^\d{10}$', 'Phone number must be exactly 10 digits.')],
        unique=True
    )
    customer_id = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    aadhar_number = models.CharField(
        max_length=12,
        unique=True,
        validators=[RegexValidator(r'^\d{12}$', 'Aadhar number must be exactly 12 digits.')]
    )
    pan = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^[A-Z]{5}\d{4}[A-Z]{1}$', 'PAN must be in the correct format (e.g., ABCDE1234F).')]
    )
    aadhar_document = models.FileField(upload_to='kyc_documents/aadhar/', blank=False, null=False)
    pan_document = models.FileField(upload_to='kyc_documents/pan/', blank=False, null=False)

    communication_address = models.TextField(blank=False)
    permanent_address = models.TextField(blank=False)

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new customer
        super().save(*args, **kwargs)
        if is_new:  # Only send email if the customer is new
            self.send_credentials_email()

    def send_credentials_email(self):
        subject = "Welcome to Our Bank!"
        message = (
            f"Dear {self.full_name},\n\n"
            f"Your account has been created successfully.\n\n"
            f"Here are your credentials:\n"
            f"Customer ID: {self.customer_id}\n"
            f"Password: {self.password}\n\n"
            f"Please keep your credentials safe.\n\n"
            f"Thank you,\n"
            f"Our Bank Team"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email="no-reply@bank.com",  # Replace with your email
                recipient_list=[self.email],
            )
        except Exception as e:
            print(f"Failed to send email to {self.email}: {str(e)}")


class CustomerAccount(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('current', 'Current'),
        ('corporate', 'Corporate'),
    ]

    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name='account',
        help_text="Each customer can only have one account."
    )
    account_number = models.CharField(
        max_length=20, unique=True, validators=[RegexValidator(r'^\d+$', 'Account number must contain only digits.')]
    )
    ifsc_code = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^[A-Z]{4}0[A-Z0-9]{6}$', 'Invalid IFSC code format.')]
    )
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    kyc_status = models.BooleanField(default=False)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.account_number} ({self.get_account_type_display()})"


# TRANSACTIONS
class CashDeposit(models.Model):
    account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE, related_name='cash_deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.account.current_balance += self.amount
        self.account.save()
        Notification.objects.create(
            recipient=self.account.customer,
            message=f"Cash deposit of {self.amount} to account {self.account.account_number}",
            notification_type='credit'
        )
        random_part = uuid.uuid4().hex[:6].upper()  # Generate a random string

        Transaction.objects.create(
            sender=None,
            receiver=self.account,
            amount=self.amount,
            transaction_type='credit',
            transaction_date=self.deposit_date,
            reference_number=f'Credit/Deposit/{random_part}'

        )

    def __str__(self):
        return f"Deposit of {self.amount} to {self.account.account_number}"


class InterBankTransfer(models.Model):
    TRANSFER_METHODS = [
        ('IMPS', 'IMPS'),
        ('NEFT', 'NEFT'),
        ('UPI', 'UPI'),
    ]

    sender_account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE, related_name='sent_transfers')
    receiver_account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE, related_name='received_transfers')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transfer_method = models.CharField(max_length=10, choices=TRANSFER_METHODS)
    transfer_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.sender_account.current_balance < self.amount:
            raise ValidationError("Insufficient funds.")
        super().save(*args, **kwargs)
        self.sender_account.current_balance -= self.amount
        self.sender_account.save()
        self.receiver_account.current_balance += self.amount
        self.receiver_account.save()
        Notification.objects.create(
            recipient=self.sender_account.customer,
            message=f"Transfer of {self.amount} from account {self.sender_account.account_number}",
            notification_type='debit'
        )
        Notification.objects.create(
            recipient=self.receiver_account.customer,
            message=f"Credited {self.amount} to account {self.receiver_account.account_number}",
            notification_type='credit'
        )
        random_part = uuid.uuid4().hex[:6].upper()  # Generate a random string
        Transaction.objects.create(
            sender=self.sender_account,
            receiver=self.receiver_account,
            amount=self.amount,
            transaction_type='debit',
            transaction_date=self.transfer_date,
            reference_number=f'{self.transfer_method}/{random_part}'
        )

    def __str__(self):
        return f"Transfer of {self.amount} from {self.sender_account.account_number} to {self.receiver_account.account_number}"


class OtherBankTransfer(models.Model):
    TRANSFER_METHODS = [
        ('IMPS', 'IMPS'),
        ('NEFT', 'NEFT'),
        ('UPI', 'UPI'),
    ]

    sender_account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE, related_name='outgoing_transfers')
    receiver_name = models.CharField(max_length=255, blank=False)
    receiver_account_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\d+$', 'Account number must contain only digits.')]
    )
    receiver_ifsc_code = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^[A-Z]{4}0[A-Z0-9]{6}$', 'Invalid IFSC code format.')]
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transfer_method = models.CharField(max_length=10, choices=TRANSFER_METHODS)
    transfer_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.sender_account.current_balance < self.amount:
            raise ValidationError("Insufficient funds.")
        super().save(*args, **kwargs)
        self.sender_account.current_balance -= self.amount
        self.sender_account.save()
        Notification.objects.create(
            recipient=self.sender_account.customer,
            message=f"Transfer of {self.amount} to external account {self.receiver_account_number} ({self.receiver_name})",
            notification_type='debit'
        )
        random_part = uuid.uuid4().hex[:6].upper()  # Generate a random string

        Transaction.objects.create(
            sender=self.sender_account,
            receiver=None,
            amount=self.amount,
            transaction_type='debit',
            transaction_date=self.transfer_date,
            reference_number=f'{self.transfer_method}/{random_part}'
        )

    def __str__(self):
        return f"Transfer of {self.amount} to {self.receiver_account_number} ({self.receiver_name})"


class Transaction(models.Model):
    sender = models.ForeignKey(CustomerAccount, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='transactions_sent')
    receiver = models.ForeignKey(CustomerAccount, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='transactions_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('credit', 'Credit'), ('debit', 'Debit')])
    transaction_date = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def __str__(self):
        return f"Transaction of {self.amount} ({self.transaction_type}) on {self.transaction_date}"


# NOTIFICATIONS
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
        ('general', 'General'),
    ]

    recipient = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(blank=False)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='general')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient.full_name} at {self.created_at}"
