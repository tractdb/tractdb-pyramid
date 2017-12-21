import cornice
import pyramid.security
import tractdb.server.accounts


def acl_authenticated(request):
    return [
        (pyramid.security.Allow, pyramid.security.Authenticated, 'authenticated'),
        pyramid.security.DENY_ALL
    ]


service_role = cornice.Service(
    name='role',
    path='/account/{id_account}/role/{id_role}',
    description='TractDB Account Role',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)

service_role_collection = cornice.Service(
    name='roles',
    path='/account/{id_account}/roles',
    description='TractDB Account Roles Collection',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)


def _get_admin(request):
    # Create our admin object
    admin = tractdb.server.accounts.AccountsAdmin(
        couchdb_url=request.registry.settings['tractdb_couchdb'],
        couchdb_admin=request.registry.settings['secrets']['couchdb']['admin']['user'],
        couchdb_admin_password=request.registry.settings['secrets']['couchdb']['admin']['password']
    )

    return admin


@service_role.delete(permission='authenticated')
def delete(request):
    """ Delete a role.
    """

    # Our account and role parameters
    account = request.matchdict['id_account']
    role = request.matchdict['id_role']

    # Our admin object
    admin = _get_admin(request)

    # Check if the account exists
    if account not in admin.list_accounts():
        request.response.status_int = 404
        return

    # Check if the role exists
    if role not in admin.list_roles(account):
        request.response.status_int = 404
        return

    # Delete the role
    admin.delete_role(account, role)

    # Return appropriately
    request.response.status_int = 200


@service_role_collection.get(permission='authenticated')
def collection_get(request):
    """ Get a list of roles.
    """

    # Our account parameter
    account = request.matchdict['id_account']

    # Our admin object
    admin = _get_admin(request)

    # Check if the account exists
    if account not in admin.list_accounts():
        request.response.status_int = 404
        return

    # Get the roles
    list_roles = admin.list_roles(account)

    # Return appropriately
    request.response.status_int = 200
    return {
        'roles':
            list_roles
    }


@service_role_collection.post(permission='authenticated')
def collection_post(request):
    """ Create an role for an account.
    """

    # Our account parameter
    account = request.matchdict['id_account']

    # Our JSON parameter, this could be validated
    json = request.json_body
    role = json['role']

    # Our admin object
    admin = _get_admin(request)

    # Check if the account exists
    if account not in admin.list_accounts():
        request.response.status_int = 404
        return

    # Check if the role exists
    if role in admin.list_roles(account):
        request.response.status_int = 409
        return

    # Create the role
    admin.add_role(account, role)

    # Return appropriately
    request.response.status_int = 201
