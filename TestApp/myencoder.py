from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise
from django.utils.encoding import force_text
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import Check
class Encoder(DjangoJSONEncoder):
    def default(self, o):                     # pylint: disable=E0202
        if isinstance(o, str):
            print("here")
            o = str(o)
            return o