#!/usr/bin/env python

import locale, time


class I18n(object):

    @staticmethod
    def get(key, inline='false'):
        if (inline == 'true'):
            return I18n._all[I18n.lang_code][key]
        else:
            return '>> ' + time.strftime("%H:%M:%S") + ' ->' + I18n._all[I18n.lang_code][key]

    _all = {
        'en_GB': {
            'only_time': '',
            'Bye': 'Bye!',
            'blind east of %s': 'This bot may be blind for all pixels east of %s',
            'blind south of %s': 'This bot may be blind for all pixels south of %s',
            'Loading chunk (%s, %s)...':'Loading chunk (%s, %s)...',
            'rad > 5 prompt': 'Are you sure do you want a radius above 5?\nIt may use a lot of resources.\ny(Yes)/anything(No)\n',
            'Saved %s': 'Saved %s',
            'Waiting %s seconds': 'Waiting %s seconds'
        }
    }

    try:
        _all[lang_code]
        lang_code = locale.getdefaultlocale(LOCALE)
    except (KeyError, NameError) as e:
        lang_code = 'en_GB'