from django.utils import timezone

from taicat.models import Species
from taicat.utils import get_species_list

ret = get_species_list(True)
now = timezone.now()
for i in ret['all']:
    if sp := Species.objects.filter(name=i[0]).first():
        sp.count = i[1]
        sp.last_updated = now
        sp.save()
    else:
        sp = Species(name=i[0], last_updated=now, count=i[1])
        if i[0] in Species.DEFAULT_LIST:
            sp.status = 'I'
        sp.save()
