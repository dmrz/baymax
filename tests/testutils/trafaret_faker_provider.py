import random

import trafaret as t
from faker.providers.python import Provider as PythonProvider
from faker.providers.internet import Provider as InternetProvider


class Provider(InternetProvider, PythonProvider):
    """
    Faker provider for trafarets. Very limited functionality yet.
    """

    def _dispatch(self, trafaret, default=None, **kwargs):
        return getattr(
            self, f"t_{trafaret.__class__.__name__.lower()}", self._default
        )(trafaret, default=default, **kwargs)

    def _default(self, trafaret, default=None, **kwargs):
        if trafaret is t.Email:
            return self.t_email(trafaret, default=default, **kwargs)
        if trafaret is t.URL:
            return self.t_url(trafaret, default=default, **kwargs)
        raise TypeError("Uknown trafaret {}".format(trafaret))

    def t_forward(self, trafaret: t.Forward, default=None, **kwargs):
        # FIXME: Not sure this forward depth is the best solution
        # to prevent max recursion depth exceptions, but works so far
        kwargs["forward_depth"] = kwargs.get("forward_depth", 0) + 1
        return self._dispatch(trafaret.trafaret, default=default, **kwargs)

    def t_dict(self, trafaret: t.Dict, default=None, **kwargs):
        if isinstance(default, dict):
            return default
        return {
            key.get_name(): self._dispatch(
                key.trafaret, default=key.default, **kwargs
            )
            for key in trafaret.keys
            # When key is optional - set a value with 50% chance (when forward depth is not very high)
            if not key.optional
            or (kwargs.get("forward_depth", 0) < 5 and random.random() > 0.5)
        }

    def t_bool(self, trafaret: t.Bool, default=None, **kwargs):
        if isinstance(default, bool):
            return default
        return self.pybool()

    def t_float(self, trafaret: t.Float, default=None, **kwargs):
        if isinstance(default, float):
            return default

        kwargs = {}
        if trafaret.gte is not None:
            kwargs["min_value"] = trafaret.gte
        if trafaret.gt is not None:
            kwargs["min_value"] = trafaret.gt + 1
        if trafaret.lte is not None:
            kwargs["max_value"] = trafaret.lte
        if trafaret.lt is not None:
            kwargs["max_value"] = trafaret.lt - 1

        return self.pyfloat(**kwargs)

    def t_email(self, trafaret: t.Email, default=None, **kwargs):
        if isinstance(default, str):
            return default
        return self.email()

    def t_url(self, trafaret: t.URL, default=None, **kwargs):
        if isinstance(default, str):
            return default
        return self.url()

    # def t_and(self, trafaret: t.Email, default=None, **kwargs):
    #     raise NotImplementedError

    # def t_or(self, trafaret: t.Email, default=None, **kwargs):
    #     raise NotImplementedError

    # def t_onerror(self, trafaret: t.Email, default=None, **kwargs):
    #     raise NotImplementedError

    def t_int(self, trafaret: t.Int, default=None, **kwargs):
        if isinstance(default, int):
            return default
        kwargs = {}
        if trafaret.gte is not None:
            kwargs["min"] = trafaret.gte
        if trafaret.gt is not None:
            kwargs["min"] = trafaret.gt + 1
        if trafaret.lte is not None:
            kwargs["max"] = trafaret.lte
        if trafaret.lt is not None:
            kwargs["max"] = trafaret.lt - 1
        return self.random_int(**kwargs)

    def t_list(self, trafaret: t.List, default=None, **kwargs):
        if isinstance(default, list):
            return default
        min_length = trafaret.min_length or 1
        max_length = trafaret.max_length or 10
        length = random.randint(min_length, max_length)
        return [self._dispatch(trafaret.trafaret) for _ in range(length)]

    def t_string(self, trafaret: t.String, default=None, **kwargs):
        if isinstance(default, str):
            return default
        # If blank string is allowed - return it with 50% chance
        if trafaret.allow_blank and random.random() > 0.5:
            return ""
        kwargs = {}
        if trafaret.min_length is not None:
            kwargs["min_chars"] = trafaret.min_length
        if trafaret.max_length is not None:
            kwargs["max_chars"] = trafaret.max_length
        return self.pystr(**kwargs)
