import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render, reverse
from django.views.generic import View
import paypalrestsdk

log = logging.getLogger(__name__)


class ShowCartView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'shop/cart.html', {
            'paypal_mode': settings.PAYPAL_MODE,
            'paypal_client_id': settings.PAYPAL_CLIENT_ID,
        })


class CheckoutView(View):
    def post(self, request, *args, **kwargs):
        paypalrestsdk.configure({
            'mode': settings.PAYPAL_MODE,
            'client_id': settings.PAYPAL_CLIENT_ID,
            'client_secret': settings.PAYPAL_CLIENT_SECRET,
        })

        payment = paypalrestsdk.Payment({
            'intent': 'sale',

            # Payer
            'payer': {
                'payment_method': 'paypal',
            },

            # Redirect URLs
            'redirect_urls': {
                'return_url': request.build_absolute_uri(reverse('shop:confirm')),
                'cancel_url': request.build_absolute_uri(reverse('shop:cart')),
            },

            # Transaction
            'transactions': [{
                # ItemList
                'item_list': {
                    'items': [{
                        'name': 'item',
                        'sku': 'item',
                        'price': '5.00',
                        'currency': 'USD',
                        'quantity': 1,
                    }]
                },
                # Amount
                'amount': {
                    'total': '5.00',
                    'currency': 'USD',
                },
                'description': 'This is the payment transaction description.',
            }]
        })

        # Create Payment and return status
        if payment.create():
            print("Payment[%s] created successfully" % (payment.id))
            # Redirect the user to given approval url
            for link in payment.links:
                if link.method == 'REDIRECT':
                    # Convert to str to avoid google appengine unicode issue
                    # https://github.com/paypal/rest-api-sdk-python/pull/58
                    redirect_url = str(link.href)
                    print("Redirect for approval: %s" % (redirect_url))
        else:
            print("Error while creating payment:")
            print(payment.error)

        return redirect(redirect_url)


class ConfirmView(View):
    def get(self, request, *args, **kwargs):
        payment_id = request.GET.get('paymentId', None)
        payer_id = request.GET.get('PayerID', None)

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            print("Got Payment Details for Payment[%s]" % (payment.id))

        except paypalrestsdk.ResourceNotFound as err:
            # It will through ResourceNotFound exception if the payment not found
            print("Payment Not Found")

        return render(request, 'shop/confirm.html', {
            'payment_id': payment_id,
            'payer_id': payer_id,
        })


class ExecuteView(View):
    def post(self, request, *args, **kwargs):
        payment_id = request.POST.get('payment_id', None)
        payer_id = request.POST.get('payer_id', None)

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except paypalrestsdk.ResourceNotFound as err:
            log.error("TODO")
            raise

        if payment.execute({'payer_id': payer_id}):
            messages.info(request, "Payment[%s] execute successfully" % payment.id)
        else:
            messages.error(request, payment.error)
            log.error("TODO")

        return render(request, 'shop/complete.html')
