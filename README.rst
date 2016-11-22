======================
Django GetOrCreatePlus
======================

Django GetOrCreatePlus is a set of queryset mixins to create custom querysets that can:

* Cache results of get_or_create() or update_or_create()

* Always use get_or_create() when get() calls are made

* Allow non-atomic get_or_create() to avoid nested transaction points

Quick start
-----------

.. code:: python

    # models.py
    
    from django.db import models
    from django.core.cache import caches
    from getorcreateplus import CachedGetOrCreateMixin, AlwaysGetOrCreateMixin, NonAtomicGetOrCreateMixin
    
    
    # sample for CachedGetOrCreateMixin (see below for changes to be made in settings.py)
    class CachedQuerySet(CachedGetOrCreateMixin, models.QuerySet):
        pass
    
    class CachedManager(models.manager.BaseManager.from_queryset(CachedQuerySet)):
        use_for_related_fields = True
    
    class CachedImmutableModel(models.Model):
        foo = models.CharField(max_length=8)
        bar = models.IntegerField(null=True)
        
        objects = CachedManager()
    
    
    obj1, _ = CachedImmutableModel.objects.get_or_create(foo='FooBar') # fetches from db
    obj2, _ = CachedImmutableModel.objects.get_or_create(foo='FooBar') # hits cache
    
    
    class CachedMutableObject(models.Model):
        foo = models.CharField(max_length=8)
        bar = models.IntegerField(null=True)
        
        objects = CachedManager()
        
        def save(self, **kwargs):
            cache = caches[self._meta.model_name]
            cache.delete(self.pk)
            return super(CachedMutableObject, self).save(**kwargs)
    
    
    obj1, _ = CachedMutableModel.objects.get_or_create(foo='FooBar') # fetches from db
    obj1.bar = 1
    obj1.save() # invalidate object cache
    obj2, _ = CachedMutableModel.objects.get_or_create(foo='FooBar') # fetches from db
    obj3, _ = CachedMutableModel.objects.get_or_create(foo='FooBar') # hits cache
    
    
    # sample for NonAtomicGetOrCreateMixin
    class NonAtomicQuerySet(NonAtomicGetOrCreateMixin, models.QuerySet):
        pass
    
    class NonAtomicManager(models.manager.BaseManager.from_queryset(NonAtomicQuerySet)):
        use_for_related_fields = True
    
    class ParentQuerySet(NonAtomicQuerySet):
        def create(self, **kwargs):
           children = kwargs.pop('children', [])
           parent = super(ParentQuerySet, self).create(**kwargs)
           for child in children:
               parent.children.get_or_create(**child)
           return parent
    
    class ParentManager(models.manager.BaseManager.from_queryset(ParentQuerySet)):
        use_for_related_fields = True
    
    class ParentModel(models.Model):
        foo = models.CharField(max_length=8)
        
        objects = ParentManager()
    
    class ChildModel(models.Model):
        parent = models.ForeignKey(Parent, related_name='children')
        bar = models.CharField(max_length=8)
        
        objects = NonAtomicManager()
    
    
    from django.db import transaction
    
    with transaction.atomic():
        parent, _ = ParentModel.objects.get_or_create(foo='Foo', defaults={children: [{bar: 'Bar'}, {bar: 'Baz'}]})
    
    
    # samples for combining mixins CachedGetOrCreateMixin, AlwaysGetOrCreateMixin, NonAtomicGetOrCreateMixin
    class NonAtomicAlwaysQuerySet(NonAtomicGetOrCreateMixin, AlwaysGetOrCreateMixin, models.QuerySet):
        pass
    
    class AlwaysCachedQuerySet(AlwaysGetOrCreateMixin, CachedGetOrCreateMixin, models.QuerySet):
        pass
    
    class PlusQuerySet(CachedGetOrCreateMixin, AlwaysGetOrCreateMixin, NonAtomicGetOrCreateMixin, models.QuerySet):
        pass

`CachedGetOrCreateMixin` uses Django caches. The keys are cached to the
`default` cache, and the objects are cached using alias
`model._meta.model_name`.

**NOTE:** If you have models by the same name in different apps both using
CachedGetOrCreateMixin, this will fail.

.. code:: python

    # settings.py
    # assuming use of django-connection-url (shameless self-plug)
    
    import connection_url
    
    CACHES = {
        'default': connection_url.config('locmem:///'),
        'cachedimmutablemodel': connection_url.config('REDIS_URL'),
        'cachedmutablemodel': connection_url.config('MEMCACHED_URL'),
    }
