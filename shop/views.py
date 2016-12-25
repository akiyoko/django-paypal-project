import logging

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.shortcuts import render, reverse
from django.views.generic import View
import paypalrestsdk

logger = logging.getLogger(__name__)


class ShowCartView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'shop/cart.html', {
            'paypal_mode': settings.PAYPAL_MODE,
        })


class CreatePaymentView(View):
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
                'return_url': request.build_absolute_uri(reverse('shop:execute-payment')),
                'cancel_url': request.build_absolute_uri(reverse('shop:cart')),
            },

            # Transaction
            # Note: This is dummy. If production, transaction should be created with reference to cart items.
            'transactions': [{
                # Item List
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

        # Create Payment
        if payment.create():
            logger.info("Payment[{}] created successfully.".format(payment.id))
            return JsonResponse({'success': True, 'paymentId': payment.id})
        else:
            logger.error("Payment failed to create. {}".format(payment.error))
            return JsonResponse({'success': False, 'error': "Error occurred while creating your payment."}, status=500)


class ExecutePaymentView(View):
    def get(self, request, *args, **kwargs):
        # Query strings are always in request.GET
        payment_id = request.GET.get('paymentId', None)
        payer_id = request.GET.get('PayerID', None)

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except paypalrestsdk.ResourceNotFound as err:
            logger.error("Payment[{}] was not found.".format(payment_id))
            return Http404

        # Execute Payment
        if payment.execute({'payer_id': payer_id}):
            logger.info("Payment[{}] executed successfully.".format(payment.id))
            messages.info(request, "Your payment has been completed successfully.")
            return render(request, 'shop/complete.html', {
                'payment': payment,
            })
        else:
            logger.error("Payment[{}] failed to execute.".format(payment.id))
            messages.error(request, "Error occurred while executing your payment.")
            return render(request, 'error.html')
