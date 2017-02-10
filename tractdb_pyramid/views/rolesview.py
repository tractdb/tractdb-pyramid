import cornice
import tractdb.server.accounts

service_role = cornice.Service(
    name='role',
    path='/account/{id_account}/roles/{id_role}',
    description='TractDB Account Role',
    cors_origins=('*',),
    cors_credentials=True
)

service_role_collection = cornice.Service(
    name='roles',
    path='/account/{id_account}/roles',
    description='TractDB Account Roles Collection',
    cors_origins=('*',),
    cors_credentials=True
)


def _get_admin(request):
    # Create our admin object
    admin = tractdb.server.accounts.AccountsAdmin(
        couchdb_url=request.registry.settings.tractdb_couchdb,
        couchdb_admin=request.registry.settings.tractdb_couchdb_secrets['admin']['user'],
        couchdb_admin_password=request.registry.settings.tractdb_couchdb_secrets['admin']['password']
    )

    return admin


@service_role.delete()
def delete(request):
    """ Delete an role.
    """

    # Our account parameter
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
    admin.delete_role(account,role)

    # Return appropriately
    request.response.status_int = 200


@service_role_collection.get()
def collection_get(request):
    """ Get a list of roles.
    """

    # Our account parameter
    account = request.matchdict['id_account']

    # Get the roles
    admin = _get_admin(request)
    list_roles = admin.list_roles(account)

    # Return appropriately
    request.response.status_int = 200
    return {
        'roles':
            list_roles
    }


@service_role_collection.post()
def collection_post(request):
    """ Create an role for an account.
    """

    # Our JSON parameter, this could be validated
    json = request.json_body
    account = json['account']
    role = json['role']

    # Our admin object
    admin = _get_admin(request)

    # Check if the account exists
    if account not in admin.list_accounts():
        request.response.status_int = 409
        return

    # Check if the role exists
    if role in admin.list_roles(account):
        request.response.status_int = 409
        return

    # Create the role
    admin.add_role(account, role)

    # Return appropriately
    request.response.status_int = 201
