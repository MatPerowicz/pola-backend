# -*- coding: utf-8 -*-

from product.models import Product
from pola.logic import create_from_api
from django.conf import settings
from produkty_w_sieci_api import Client
from django.utils import timezone
from datetime import timedelta

REQUERY_590_FREQUENCY = 7
REQUERY_590_LIMIT = 100
REQUERY_ALL_FREQUENCY = 30
REQUERY_ALL_LIMIT = 100

# usage:
# python manage.py shell
# from pola.logic_workers import requery_590_codes
# requery_590_codes()

#update product_product set ilim_queried_at='2015/11/11'

#requery products without company, 590-codes, last queried more then 7 days ago
def requery_590_codes():
    print "Starting requering 590 codes..."

    p590 = Product.objects\
        .filter(company__isnull=True, code__startswith='590',
                ilim_queried_at__lt=
                timezone.now()-timedelta(days=REQUERY_590_FREQUENCY))\
                [:REQUERY_590_LIMIT]

    requery_products(p590)

    print "Finished requering 590 codes..."

def requery_all_codes():
    print "Starting requering all codes..."

    products = Product.objects\
        .filter(ilim_queried_at__lt=
                timezone.now()-timedelta(days=REQUERY_ALL_FREQUENCY))\
                [:REQUERY_ALL_LIMIT]

#    products = Product.objects.filter(code='142222157008')

    requery_products(products)

    print "Finished requering all codes..."

def requery_products(products):
    client = Client(settings.PRODUKTY_W_SIECI_API_KEY)

    for prod in products:
        print prod.code + " -> ",

        prod.ilim_queried_at = timezone.now()
        prod.save()

        if prod.code.isdigit() and\
            (len(prod.code) == 8 or len(prod.code) == 13):
            product_info = client.get_product_by_gtin(prod.code)

            p = create_from_api(prod.code, product_info, product=prod)

            if p.company and p.company.name:
                print p.company.name.encode('utf-8')
            else:
                print "."
        else:
            print ";"