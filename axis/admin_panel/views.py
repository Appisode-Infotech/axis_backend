from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import random
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from rest_framework import viewsets
from .models import Transaction
from .serializers import TransactionSerializer

from .models import Customer, CustomerAccount, CashDeposit, InterBankTransfer, OtherBankTransfer, Notification
from .serializers import (
    CustomerSerializer, CustomerAccountSerializer, CashDepositSerializer,
    InterBankTransferSerializer, OtherBankTransferSerializer, NotificationSerializer
)

from django.db import transaction
from rest_framework.exceptions import ValidationError, NotFound


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    parser_classes = [MultiPartParser, FormParser]


class CustomerAccountViewSet(viewsets.ModelViewSet):
    queryset = CustomerAccount.objects.all()
    serializer_class = CustomerAccountSerializer


class CashDepositViewSet(viewsets.ModelViewSet):
    queryset = CashDeposit.objects.all()
    serializer_class = CashDepositSerializer


class InterBankTransferViewSet(viewsets.ModelViewSet):
    queryset = InterBankTransfer.objects.all()
    serializer_class = InterBankTransferSerializer


class OtherBankTransferViewSet(viewsets.ModelViewSet):
    queryset = OtherBankTransfer.objects.all()
    serializer_class = OtherBankTransferSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class LoginAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Login API for customers",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'customer_id': openapi.Schema(type=openapi.TYPE_STRING, description='Customer ID'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'pan': openapi.Schema(type=openapi.TYPE_STRING, description='PAN number'),
            },
            required=['customer_id', 'password', 'pan'],
        ),
        responses={
            200: CustomerSerializer(),
            400: 'Bad Request',
            401: 'Unauthorized - Invalid credentials',
        },
    )
    def post(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        password = request.data.get('password')
        pan = request.data.get('pan')

        if not all([customer_id, password, pan]):
            return Response(
                {"error": "All fields (customer_id, password, pan) are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            customer = Customer.objects.get(customer_id=customer_id, password=password, pan=pan)
            serializer = CustomerSerializer(customer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Customer.DoesNotExist:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class GenerateOTPAPIView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate a 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"

        # Send the OTP email
        # try:
        #     send_mail(
        #         subject="Your OTP Code",
        #         message=f"Your OTP code is {otp}.",
        #         from_email="your_email@gmail.com",  # Replace with your email address
        #         recipient_list=[email],
        #     )
        # except Exception as e:
        #     return Response(
        #         {"error": f"Failed to send OTP: {str(e)}"},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

        # Return the OTP in the response
        print(otp)
        return Response(
            {"otp": otp, "message": "OTP sent successfully."},
            status=status.HTTP_200_OK,
        )


class TransactionViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and managing transaction instances.
    """
    queryset = Transaction.objects.all().order_by('-transaction_date')
    serializer_class = TransactionSerializer


class UserTransactionsAPIView(APIView):
    """
    API to fetch all transactions for a specific user.
    """

    def get(self, request, customer_id, *args, **kwargs):
        try:
            # Fetch the customer
            customer = Customer.objects.get(customer_id=customer_id)
            customer_serializer = CustomerSerializer(customer)

            # Get all accounts for the customer
            accounts = CustomerAccount.objects.filter(customer=customer)
            accounts_serializer = CustomerAccountSerializer(accounts, many=True)

            # Get all transactions where the user's accounts are involved
            transactions = Transaction.objects.filter(
                Q(sender__in=accounts) | Q(receiver__in=accounts)
            ).distinct().order_by('-transaction_date')
            # Serialize the transactions
            transaction_serializer = TransactionSerializer(transactions, many=True)

            return Response(
                {
                    "customer": customer_serializer.data,
                    "accounts": accounts_serializer.data,
                    "transactions": transaction_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Customer.DoesNotExist:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)


class CustomerNotificationsAPIView(APIView):
    """
    API to fetch all notifications for a specific customer by customer_id.
    """

    def get(self, request, customer_id, *args, **kwargs):
        try:
            # Get the customer object by customer_id (case-insensitive)
            customer = Customer.objects.get(customer_id__iexact=customer_id)

            # Retrieve all notifications for the customer
            notifications = Notification.objects.filter(recipient=customer).order_by('-created_at')

            # Serialize the notifications
            serializer = NotificationSerializer(notifications, many=True)
            return Response(
                {
                    "notifications": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
            # Return the serialized notifications

        except Customer.DoesNotExist:
            # Return a 404 if the customer does not exist
            return Response(
                {"error": f"Customer with ID '{customer_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Handle unexpected errors
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class GetAccountDetailsView(APIView):
    @swagger_auto_schema(
        operation_summary="Get Customer Account Details",
        operation_description="Retrieve account details by providing the customer's phone number.",
        responses={
            200: CustomerAccountSerializer,
            404: "Customer or account not found.",
        },
        manual_parameters=[
            openapi.Parameter(
                'phone_number', openapi.IN_PATH, type=openapi.TYPE_STRING,
                description="Customer's phone number (10 digits)"
            )
        ]
    )
    def get(self, request, phone_number):
        try:
            customer = Customer.objects.get(phone_number=phone_number)
            account = customer.account
            serializer = CustomerAccountSerializer(account)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            raise NotFound("Customer with this phone number does not exist.")
        except CustomerAccount.DoesNotExist:
            raise NotFound("Account details for this customer are not available.")


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class GetAccountDetailsByAccountNumberView(APIView):
    @swagger_auto_schema(
        operation_summary="Get Account Details by Account Number",
        operation_description="Retrieve account details by providing the customer's account number.",
        responses={
            200: CustomerAccountSerializer,
            404: "Account not found.",
        },
        manual_parameters=[
            openapi.Parameter(
                'account_number', openapi.IN_PATH, type=openapi.TYPE_STRING,
                description="Customer's account number"
            )
        ]
    )
    def get(self, request, account_number):
        try:
            account = CustomerAccount.objects.get(account_number=account_number)
            serializer = CustomerAccountSerializer(account)
            return Response(serializer.data)
        except CustomerAccount.DoesNotExist:
            raise NotFound("Account with this account number does not exist.")


class HandlePaymentAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Handle Payment",
        operation_description=(
                "Handles a payment request. If the payee exists within the bank, an internal transfer is processed. "
                "Otherwise, an external bank transfer is initiated."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "amount": openapi.Schema(type=openapi.TYPE_NUMBER, description="Transfer amount."),
                "remark": openapi.Schema(type=openapi.TYPE_STRING, description="Transaction remark.", default=""),
                "paymentType": openapi.Schema(type=openapi.TYPE_STRING, description="Payment type (e.g., 'Pay Now')."),
                "paymentMode": openapi.Schema(type=openapi.TYPE_STRING, description="Payment mode (e.g., 'IMPS')."),
                "payee": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "account_number": openapi.Schema(type=openapi.TYPE_STRING,
                                                         description="Payee's account number."),
                        "ifsc_code": openapi.Schema(type=openapi.TYPE_STRING, description="Payee's IFSC code."),
                        "customer": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Payee's full name.")
                            }
                        )
                    }
                ),
                "source_customer_id": openapi.Schema(type=openapi.TYPE_STRING, description="Source customer ID."),
            },
            required=["amount", "payee", "source_customer_id"],
        ),
        responses={
            200: "Payment processed successfully.",
            400: "Bad request or validation error.",
            404: "Customer or account not found.",
        }
    )
    def post(self, request):
        payload = request.data
        try:
            # Extract details from the payload
            amount = int(payload.get("amount"))
            payment_mode = payload.get("paymentMode")
            payee_details = payload.get("payee")
            source_customer_id = payload.get("source_customer_id")

            if not all([amount, payment_mode, payee_details, source_customer_id]):
                raise ValidationError("Missing required fields in the payload.")
            print("case1")
            # Fetch source customer and account
            try:
                print("case2")
                source_customer = Customer.objects.get(customer_id=source_customer_id)
                print("case3")
                source_account = CustomerAccount.objects.get(customer=source_customer)
                print("case4")
            except Customer.DoesNotExist:
                print("case5")
                raise NotFound("Source customer not found.")
            except CustomerAccount.DoesNotExist:
                print("case7")
                raise NotFound("Source account not found.")
            print("case8")

            payee_account_number = payee_details.get("account_number")
            payee_ifsc_code = payee_details.get("ifsc_code")

            # Determine if the payee is within the bank
            try:
                # Internal transfer
                payee_account = CustomerAccount.objects.get(account_number=payee_account_number,
                                                            ifsc_code=payee_ifsc_code)
                print(payee_account)
                with transaction.atomic():
                    interbank_transfer = InterBankTransfer.objects.create(
                        sender_account=source_account,
                        receiver_account=payee_account,
                        amount=amount,
                        transfer_method=payment_mode,
                    )
                    print(interbank_transfer)
                    return Response(
                        {"message": "Internal transfer processed successfully.",
                         "transaction": InterBankTransferSerializer(interbank_transfer).data},
                        status=status.HTTP_200_OK,
                    )
            except CustomerAccount.DoesNotExist:
                # External transfer
                payee_name = payee_details.get("customer", {}).get("full_name")
                with transaction.atomic():
                    external_transfer = OtherBankTransfer.objects.create(
                        sender_account=source_account,
                        receiver_name=payee_name,
                        receiver_account_number=payee_account_number,
                        receiver_ifsc_code=payee_ifsc_code,
                        amount=amount,
                        transfer_method=payment_mode,
                    )
                    return Response(
                        {"message": "External transfer processed successfully.",
                         "transaction": OtherBankTransferSerializer(external_transfer).data},
                        status=status.HTTP_200_OK,
                    )

        except ValidationError as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({"error": f"An unexpected error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
