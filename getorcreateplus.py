"""
Copyright 2016 Vimal Aravindashan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

try:
    from xxhash import xxh64 as key_fn
except ImportError:
    from hashlib import md5 as key_fn
from django.core.cache import caches

def cached_select(func):
    def actual_func(self, defaults=None, **kwargs):
        key_cache = caches['default']
        key = key_fn(repr(sorted(kwargs.items()))).hexdigest()
        obj_pk = key_cache.get(key) if not kwargs.pop('force_select', False) else None
        obj_cache = caches[self.model._meta.model_name]
        obj, created = obj_cache.get(obj_pk) if obj_pk else None, False
        if not obj:
            obj, created = func(self, defaults=defaults, **kwargs)
            obj_cache.set(obj.pk, obj)
            key_cache.set(key, obj.pk)
        return obj, created
    return actual_func

class CachedGetOrCreateMixin(object):
    @cached_select
    def get_or_create(self, defaults=None, **kwargs):
        return super(CachedGetOrCreateMixin, self).get_or_create(defaults=defaults, **kwargs)
    
    @cached_select
    def update_or_create(self, defaults=None, **kwargs):
        return super(CachedGetOrCreateMixin, self).update_or_create(defaults=defaults, **kwargs)

class AlwaysGetOrCreateMixin(object):
    def get(self, *args, **kwargs):
        if self._for_write == True:
            obj = super(AlwaysGetOrCreateMixin, self).get(*args, **kwargs)
        else:
            obj, _ = self.get_or_create(**kwargs)
        return obj

class NonAtomicGetOrCreateMixin(object):
    def _create_object_from_params(self, lookup, params):
        """
        Creates an object using passed params.
        Atomicity is optional, and the caller is responsible.
        Used by get_or_create and update_or_create
        """
        return self.create(**params), True
