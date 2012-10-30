from functools import wraps

from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

import jingo
from product_details.version_compare import Version
from session_csrf import anonymous_csrf_exempt
from tower import ugettext as _

import input
from input.decorators import cache_page, forward_mobile
from input.urlresolvers import reverse
from feedback.forms import PraiseForm, IssueForm, IdeaForm
from feedback.models import Opinion
from feedback.utils import detect_language, ua_parse


def enforce_ua(f):
    """
    View decorator enforcing feedback from the right (latest beta, latest
    release) users only.

    Can be disabled with settings.ENFORCE_USER_AGENT = False.
    """
    @wraps(f)
    def wrapped(request, *args, **kwargs):
        # Validate User-Agent request header.
        ua = request.META.get('HTTP_USER_AGENT', None)
        parsed = ua_parse(ua)

        if not parsed:  # Unknown UA.
            if request.method == 'GET':
                return http.HttpResponseRedirect(
                        reverse('feedback.download'))
            else:
                return http.HttpResponseBadRequest(
                    _('User-Agent request header must be set.'))

        if not settings.ENFORCE_USER_AGENT:
            return f(request, ua=ua, *args, **kwargs)

        this_ver = Version(parsed['version'])
        ref_ver = Version(parsed['browser'].min_version)
        # Check for outdated release.
        if this_ver < ref_ver:
            return http.HttpResponseRedirect(reverse('feedback.download'))

        # If we made it here, it's a valid version.
        return f(request, ua=ua, *args, **kwargs)

    return wrapped


@forward_mobile
@enforce_ua
@never_cache
@anonymous_csrf_exempt
def feedback(request, ua):
    """Page to receive feedback under happy/sad/idea categories"""
    initial = dict(url=request.REQUEST.get('url'))

    if request.method == 'POST':
        typ = int(request.POST.get('_type'))

        if typ == input.OPINION_PRAISE.id:
            form = PraiseForm(request.POST, auto_id='happy-%s')
        elif typ == input.OPINION_ISSUE.id:
            form = IssueForm(request.POST, auto_id='sad-%s')
        else:
            form = IdeaForm(request.POST, auto_id='idea-%s')

        if form.is_valid():
            request.session['previous_opinion'] = save_opinion_from_form(
                                                    request, typ, ua, form)

            url = reverse('thanks')
            return http.HttpResponseRedirect(url)

        else:
            forms = {'happy': (form if typ == input.OPINION_PRAISE.id else
                               PraiseForm(auto_id='happy-%s', initial=initial)),
                     'sad': (form if typ == input.OPINION_ISSUE.id else
                             IssueForm(auto_id='sad-%s', initial=initial)),
                     'idea': (form if typ == input.OPINION_IDEA.id else
                              IdeaForm(auto_id='idea-%s'))}
    else:
        forms = {'happy': PraiseForm(auto_id='happy-%s', initial=initial),
                 'sad': IssueForm(auto_id='sad-%s', initial=initial),
                 'idea': IdeaForm(auto_id='idea-%s')}

    template = 'feedback/%sindex.html' % (
        'mobile/' if request.mobile_site else '')
    return render(request, template, {'forms': forms, 'locale': request.locale})


@cache_page
def download(request):
    """Encourage people to download a current version."""

    template = 'feedback/%sdownload.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template)


@never_cache
def thanks(request):
    """Thank you for your feedback."""

    try:
        previous_opinion = request.session['previous_opinion']
    except KeyError:
        previous_opinion = None

    template = 'feedback/%sthanks.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template, {'opinion': previous_opinion})


@forward_mobile
@cache_page
def opinion_detail(request, id):
    o = get_object_or_404(Opinion, pk=id, _type__in=input.OPINION_TYPES.keys())

    if not request.mobile_site:
        template = 'feedback/opinion.html'
    else:
        template = 'feedback/mobile/opinion.html'
    return jingo.render(request, template, {'opinion': o})


def save_opinion_from_form(request, type, ua, form):
    """Given a (valid) form and feedback type, save it to the DB."""
    locale = detect_language(request)

    if type not in input.OPINION_TYPES:
        raise ValueError('Unknown type %s' % type)

    opinion = Opinion(
        _type=type,
        url=form.cleaned_data.get('url') or '',
        description=form.cleaned_data['description'],
        user_agent=ua,
        locale=locale,
        manufacturer=form.cleaned_data['manufacturer'],
        device=form.cleaned_data['device'])
    opinion.save()

    return opinion
