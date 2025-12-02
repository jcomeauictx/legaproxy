#!/usr/bin/python3
'''
blinker._saferef monkeypatch for mitmdump (mitmproxy) before 8.1.1-4

(Debian trixie has 8.1.1-2)

after importing, patch blinker thus:

try:
    from blinker import _saferef
except ImportError:
    blinker._saferef = sys.modules['_saferef'] 

code and patch suggested by claude.ai, Sonnet 4.5.
'''
import weakref

def saferef(target, on_delete=None):
    '''
    return a safe weak reference to a callable target
    '''
    try:
        im_self = target.__self__
    except AttributeError:
        # not a bound method, just use regular weakref
        if callable(on_delete):
            return weakref.ref(target, on_delete)
        else:
            return weakref.ref(target)
    else:
        if im_self is not None:
            # it's a bound method
            return BoundMethodWeakref(target=target, on_delete=on_delete)

class BoundMethodWeakref:
    '''
    weak reference to a bound method
    '''
    _all_instances = weakref.WeakValueDictionary()
    
    def __new__(cls, target, on_delete=None):
        key = cls.calculate_key(target)
        current = cls._all_instances.get(key)
        if current is not None:
            current.deletion_methods.append(on_delete)
            return current
        else:
            instance = super().__new__(cls)
            cls._all_instances[key] = instance
            instance.__init__(target, on_delete)
            return instance
    
    def __init__(self, target, on_delete=None):
        if hasattr(self, 'deletion_methods'):
            return  # Already initialized
        
        def remove(weak, self=self):
            methods = self.deletion_methods[:]
            del self.deletion_methods[:]
            try:
                del self.__class__._all_instances[self.key]
            except KeyError:
                pass
            for function in methods:
                if callable(function):
                    try:
                        function(self)
                    except Exception:
                        pass
        
        self.deletion_methods = [on_delete]
        self.key = self.calculate_key(target)
        im_self = target.__self__
        im_func = target.__func__
        self.weak_self = weakref.ref(im_self, remove)
        self.weak_func = weakref.ref(im_func, remove)
    
    @classmethod
    def calculate_key(cls, target):
        return (id(target.__self__), id(target.__func__))
    
    def __call__(self):
        '''
        return a strong reference to the bound method
        '''
        target = self.weak_self()
        if target is not None:
            function = self.weak_func()
            if function is not None:
                return function.__get__(target)
        return None
