'''
tag_cloud
===================================
This plugin generates a tag cloud for each category from available tags
'''
from __future__ import unicode_literals

from collections import defaultdict
from operator import itemgetter

import logging
import math
import random

from pelican import signals

logger = logging.getLogger(__name__)


def set_default_settings(settings):
    settings.setdefault('TAG_CLOUD_STEPS', 4)
    settings.setdefault('TAG_CLOUD_MAX_ITEMS', 50)
    settings.setdefault('TAG_CLOUD_SORTING', 'size')
    settings.setdefault('TAG_CLOUD_BADGE', True)


def init_default_config(pelican):
    from pelican.settings import DEFAULT_CONFIG
    set_default_settings(DEFAULT_CONFIG)
    if(pelican):
            set_default_settings(pelican.settings)

def generate_tag_cloud(generator):
    tag_cloud = dict()
    for article in generator.articles:
        cat = getattr(article, 'category', [])
        for tag in getattr(article, 'tags', []):
            if not cat in tag_cloud:
                tag_cloud[cat] = defaultdict(int)
            tag_cloud[cat][tag] += 1

    for cat in tag_cloud:
        tag_cloud[cat] = sorted(tag_cloud[cat].items(), key=itemgetter(1), reverse=True)
        tag_cloud[cat] = tag_cloud[cat][:generator.settings.get('TAG_CLOUD_MAX_ITEMS')]

        tags = list(map(itemgetter(1), tag_cloud[cat]))
        if tags:
            max_count = max(tags)
        steps = generator.settings.get('TAG_CLOUD_STEPS')

        # calculate word sizes
        def generate_tag(tag, count):
            tag = (
                tag,
                int(math.floor(steps - (steps - 1) * math.log(count)
                    / (math.log(max_count)or 1)))
            )
            if generator.settings.get('TAG_CLOUD_BADGE'):
                tag += (count,)
            return tag

        tag_cloud[cat] = [
            generate_tag(tag, count)
            for tag, count in tag_cloud[cat]
        ]

        sorting = generator.settings.get('TAG_CLOUD_SORTING')

        if sorting == 'alphabetically':
            tag_cloud[cat].sort(key=lambda elem: elem[0].name)
        elif sorting == 'alphabetically-rev':
            tag_cloud[cat].sort(key=lambda elem: elem[0].name, reverse=True)
        elif sorting == 'size':
            tag_cloud[cat].sort(key=lambda elem: elem[1])
        elif sorting == 'size-rev':
            tag_cloud[cat].sort(key=lambda elem: elem[1], reverse=True)
        elif sorting == 'random':
            random.shuffle(tag_cloud[cat])
        else:
            logger.warning("setting for TAG_CLOUD_SORTING not recognized: %s, "
                           "falling back to 'random'", sorting)
            random.shuffle(tag_cloud[cat])
    
    #Pelican doesn't allow dictionaries! Have to listify this
    tag_cloud = list(tag_cloud.items())    
        
    # make available in context
    generator.tag_cloud = tag_cloud
    generator._update_context(['tag_cloud'])

def register():
    signals.initialized.connect(init_default_config)
    signals.article_generator_finalized.connect(generate_tag_cloud)