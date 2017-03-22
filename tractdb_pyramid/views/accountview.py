import cornice
import tractdb.server.accounts

service_account = cornice.Service(
    name='account',
    path='/account/{id_account}',
    description='TractDB Account',
    cors_origins=('*',),
    cors_credentials=True
)

service_account_collection = cornice.Service(
    name='accounts',
    path='/accounts',
    description='TractDB Account Collection',
    cors_origins=('*',),
    cors_credentials=True
)

service_reset_password = cornice.Service(
    name='reset_password',
    path='/reset_password',
    description='TractDB Reset Password',
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


@service_account.delete()
def delete(request):
    """ Delete an account.
    """

    # Our account parameter
    account = request.matchdict['id_account']

    # Our admin object
    admin = _get_admin(request)

    # Check if the account exists
    if account not in admin.list_accounts():
        request.response.status_int = 404
        return

    # Delete the account
    admin.delete_account(account)

    # Return appropriately
    request.response.status_int = 200


@service_account_collection.get()
def collection_get(request):
    """ Get a list of accounts.
    """
    # Get the accounts
    admin = _get_admin(request)
    list_accounts = admin.list_accounts()

    # Return appropriately
    request.response.status_int = 200
    return {
        'accounts':
            list_accounts
    }


@service_account_collection.post()
def collection_post(request):
    """ Create an account.
    """

    # Our JSON parameter, this could be validated
    json = request.json_body
    account = json['account']
    account_password = json['password']

    # Our admin object
    admin = _get_admin(request)

    # Check if the account exists
    if account in admin.list_accounts():
        request.response.status_int = 409
        return

    # Create the account
    admin.create_account(account, account_password)

    # Return appropriately
    request.response.status_int = 201


# service_reset_password = cornice.Service(
#     name='reset_password',
#     path='/reset_password',
#     description='TractDB Reset Password',
#     cors_origins=('*',),
#     cors_credentials=True
# )
#
# @service_reset_password.post()
# def reset_password_post(request):
#     """ Reset password of an account.
#     """
#
#     # Our JSON parameter, this could be validated
#     json = request.json_body
#     account = json['account']
#     account_password = json['password']
#
#     # Our admin object
#     admin = _get_admin(request)
#
#
#     # Check if the account does not exist
#     if account not in admin.list_accounts():
#         request.response.status_int = 409
#         return
#
#     # Reset the password
#     admin.reset_password(account, account_password)
#
#     # Return appropriately
#     request.response.status_int = 201

