# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import Count
from django.db.models import Q
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _
from model_utils.managers import PassThroughManager
from django.core.validators import ValidationError
import reversion
from pola.concurency import concurency
from sets import Set


class IntegerRangeField(models.IntegerField):

    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        super(models.IntegerField, self).__init__(*args, **kwargs)
        self.min_value, self.max_value = min_value, max_value

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value,
                    'max_value': self.max_value}
        defaults.update(kwargs)
        return super(IntegerRangeField, self).formfield(**defaults)


class CompanyQuerySet(models.query.QuerySet):

    def get_or_create(self, commit_desc=None, commit_user=None,
                      *args, **kwargs):
        if not commit_desc:
            return super(CompanyQuerySet, self).get_or_create(*args, **kwargs)

        with transaction.atomic(), reversion.create_revision(
                manage_manually=True):
            obj = super(CompanyQuerySet, self).get_or_create(*args, **kwargs)
            reversion.default_revision_manager.\
                save_revision([obj[0]], comment=commit_desc, user=commit_user)
            return obj

    def search_by_name(self, keyword):
        where = Q(name__icontains=keyword)
        where = where | Q(official_name__icontains=keyword)
        where = where | Q(common_name__icontains=keyword)
        where = where | Q(brand__name__icontains=keyword)
        if self.isEan(keyword):
                where = where | Q(product__code=keyword)
        return self.filter(where).distinct('id').prefetch_related('brand_set')

    def isEan(self, keyword):
        return keyword.isdigit() and (len(keyword) == 13 or len(keyword) == 8)

    def with_query_count(self):
        return self.annotate(query_count=Count('product__query__id'))


class Company(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=128,
                            null=True,
                            blank=True,
                            db_index=True,
                            verbose_name=_(u"Nazwa (pobrana z ILiM)"))
    official_name = models.CharField(max_length=128,
                                     db_index=True,
                                     blank=True,
                                     null=True,
                                     verbose_name=_(u"Nazwa rejestrowa"))
    common_name = models.CharField(max_length=128,
                                   db_index=True,
                                   blank=True,
                                   verbose_name=_(u"Nazwa dla użytkownika"))

    plCapital = IntegerRangeField(
        verbose_name=_(u"Udział polskiego kapitału"),
        min_value=0, max_value=100, null=True, blank=True)
    plWorkers = IntegerRangeField(
        verbose_name=_(u"Miejsce produkcji"), min_value=0,
        max_value=100, null=True, blank=True,
        choices=((0, _(u"0 - Nie produkuje w Polsce")),
                 (100, _(u"100 - Produkuje w Polsce"))))
    plRnD = IntegerRangeField(
        verbose_name=_(u"Miejsca pracy w BiR w Polsce"), min_value=0,
        max_value=100, null=True, blank=True,
        choices=((0, _(u"0 - Nie tworzy miejsc pracy w BiR Polsce")),
                 (100, _(u"100 - Tworzy miejsca pracy w BiR w Polsce"))))
    plRegistered = IntegerRangeField(
        verbose_name=_(u"Miejsce rejestracji"), min_value=0, max_value=100,
        null=True, blank=True,
        choices=((0, _(u"0 - Firma zarejestrowana za granicą")),
                 (100, _(u"100 - Firma zarejestrowana w Polsce"))))
    plNotGlobEnt = IntegerRangeField(
        verbose_name=_(u"Struktura kapitałowa"), min_value=0,
        max_value=100, null=True, blank=True,
        choices=((0, _(u"0 - Firma jest częścią zagranicznego koncernu")),
                 (100,
                  _(u"100 - Firma nie jest częścią zagranicznego koncernu"))))

    description = models.TextField(
        _(u"Opis producenta"), null=True, blank=True)
    sources = models.TextField(_(u"Źródła"), null=True, blank=True)

    verified = models.BooleanField(default=False,
                                   verbose_name=_("Dane zweryfikowane"),
                                   choices=((True, _("Tak")),
                                            (False, _("Nie"))))

    Editor_notes = models.TextField(
        _(u"Notatki redakcji (nie pokazujemy użytkownikom)"), null=True,
        blank=True)

    plCapital_notes = models.TextField(
        _(u"Więcej nt. udziału polskiego kapitału"), null=True, blank=True)
    plWorkers_notes = models.TextField(
        _(u"Więcej nt. miejsca produkcji"), null=True, blank=True)
    plRnD_notes = models.TextField(
        _(u"Więcej nt. miejsc pracy w BiR"), null=True, blank=True)
    plRegistered_notes = models.TextField(
        _(u"Więcej nt. miejsca rejestracji"), null=True, blank=True)
    plNotGlobEnt_notes = models.TextField(
        _(u"Więcej nt. struktury kapitałowej"), null=True, blank=True)

    nip = models.CharField(max_length=10, db_index=True, null=True,
                           blank=True, verbose_name=_(u"NIP/Tax ID"))
    address = models.TextField(null=True, blank=True,
                               verbose_name=_(u"Adres"))

    objects = PassThroughManager.for_queryset_class(CompanyQuerySet)()

    def to_dict(self):
        dict = model_to_dict(self)
        return dict

    def get_absolute_url(self):
        return reverse('company:detail', args=[self.pk])

    def locked_by(self):
        return concurency.locked_by(self)

    def get_brands(self):
        return set([x.name for x in self.brand_set.all()])

    def set_brands(self, new_names_str):
        new_names = [x.strip() for x in new_names_str.split(',')]

        new_names = set(new_names)
        curr_names = set(self.get_brands())

        to_delete = curr_names - new_names
        to_add = new_names - curr_names

        from brand.models import Brand
        new_brands = [Brand(name=x, company=self) for x in to_add]

        self.brand_set.bulk_create(new_brands)
        self.brand_set.filter(name__in=to_delete).delete()

    def __unicode__(self):
        return self.common_name or self.official_name or self.name

    def js_plCapital_notes(self):
        return '' if not self.plCapital_notes else\
            self.plCapital_notes.replace('\n', '\\n').replace('\r', '\\r')

    def js_plWorkers_notes(self):
        return '' if not self.plWorkers_notes else\
            self.plWorkers_notes.replace('\n', '\\n').replace('\r', '\\r')

    def js_plRnD_notes(self):
        return '' if not self.plRnD_notes else\
            self.plRnD_notes.replace('\n', '\\n').replace('\r', '\\r')

    def js_plRegistered_notes(self):
        return '' if not self.plRegistered_notes else\
            self.plRegistered_notes.replace('\n', '\\n').replace('\r', '\\r')

    def js_plNotGlobEnt_notes(self):
        return '' if not self.plNotGlobEnt_notes else\
            self.plNotGlobEnt_notes.replace('\n', '\\n').replace('\r', '\\r')

    def get_sources(self, raise_exp=True):
        ret = {}
        if not self.sources:
            return ret

        lines = self.sources.splitlines()
        for line in lines:
            line = line.strip()
            if line == u'':
                continue
            s = line.split(u'|')
            if s.__len__() != 2:
                if raise_exp:
                    raise ValidationError(u'Pole >Źródła< powinno składać się '
                                          u'linii zawierających tytuł odnośnika'
                                          u' i odnośnik odzielone znakiem | (pipe)')
                else:
                    continue
            if s[0] in ret:
                if raise_exp:
                    raise ValidationError(u'Tytuł odnośnika >{}< występuje'
                                          u' więcej niż raz'.format(s[0]))
                else:
                    continue
            ret[s[0]] = s[1]

        return ret

    def clean(self, *args, **kwargs):
        if self.verified:
            YOU_CANT_SET_VERIFIED = u'Nie możesz oznaczyć producenta jako ' \
                u'zweryfikowany jeśli pole >{}< jest nieustalone'
            if self.plCapital is None:
                raise ValidationError(YOU_CANT_SET_VERIFIED.
                                      format(u'udział kapitału polskiego'))
            if self.plWorkers is None:
                raise ValidationError(YOU_CANT_SET_VERIFIED.
                                      format(u'miejsce produkcji'))
            if self.plRnD is None:
                raise ValidationError(YOU_CANT_SET_VERIFIED.
                                      format('wysokopłatne miejsca pracy'))
            if self.plRegistered is None:
                raise ValidationError(YOU_CANT_SET_VERIFIED.
                                      format(u'miejsce rejestracji'))
            if self.plNotGlobEnt is None:
                raise ValidationError(YOU_CANT_SET_VERIFIED.
                                      format(u'struktura kapitałowa'))
            self.get_sources()

        super(Company, self).clean(*args, **kwargs)

    def save(self, commit_desc=None, commit_user=None, *args, **kwargs):
        self.full_clean()
        if not commit_desc:
            return super(Company, self).save(*args, **kwargs)

        with transaction.atomic(), reversion.\
                create_revision(manage_manually=True):
            obj = super(Company, self).save(*args, **kwargs)
            reversion.default_revision_manager.\
                save_revision([self], comment=commit_desc, user=commit_user)
            return obj

    class Meta:
        verbose_name = _(u"Producent")
        verbose_name_plural = _(u"Producenci")

reversion.register(Company)
