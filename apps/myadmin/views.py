from django.contrib import admin
from django.shortcuts import redirect, render
from django.views import debug

import api.tasks
import themes.tasks


# TODO(davedash): remove when metrics.json is in place
def recluster(request):
    if request.method == 'POST':
        themes.tasks.recluster.delay()
        return redirect('myadmin.recluster')

    return render(request, 'myadmin/recluster.html')
admin.site.register_view('recluster', recluster, urlname='myadmin.recluster')


def export_tsv(request):
    if request.method == 'POST':
        api.tasks.export_tsv.delay()
        data = {'exporting': True}
    else:
        data = {}

    return render(request, 'myadmin/export_tsv.html', data)
admin.site.register_view('export_tsv', export_tsv, urlname='myadmin.export_tsv')


def settings(request):
    settings_dict = debug.get_safe_settings()

    return render(request, 'myadmin/settings.html',
                        {'settings_dict': settings_dict})
admin.site.register_view('settings', settings, urlname='myadmin.settings')
