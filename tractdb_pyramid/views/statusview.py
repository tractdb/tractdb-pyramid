import cornice
import requests

service = cornice.Service(
    name='status',
    path='/',
    description='TractDB Status',
    cors_origins=('*',),
    cors_credentials=True
)


@service.get()
def get(request):
    return {
        'status':
            'ready',
        'couchdb':
            requests.get(
                request.registry.settings['tractdb_couchdb']
            ).json()
    }
