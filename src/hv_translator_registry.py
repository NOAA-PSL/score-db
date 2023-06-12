"""
Copyright 2023 NOAA
All rights reserved.

Collection translator handlers registrations.  This module helps define
the translator handler format as well as the module definitions for each
translator type

"""

from collections import namedtuple
import harvest_translator

TranslatorHandler = namedtuple(
    'TranslatorHandler',
    [
        'description',
        'translate'
    ],
)

translator_registry = {
    'inc_logs': TranslatorHandler(
        'translate harvest values from inc_logs harvester',
        harvest_translator.inc_logs_translator
    ),
}

valid_translators = list(translator_registry.keys())

