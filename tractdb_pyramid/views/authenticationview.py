import cornice
import pyramid.security
import pyramid.view
import requests

################################################################################
# A simple service that is accessible only when authenticated.
################################################################################


def acl_authenticated(request):
    return [
        (pyramid.security.Allow, pyramid.security.Authenticated, 'authenticated'),
        pyramid.security.DENY_ALL
    ]

service_authenticated = cornice.Service(
    name='authenticated',
    path='/authenticated',
    description='TractDB Authenticated',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)


@service_authenticated.get(permission='authenticated')
def authenticated_get(request):
    return {
        'account':
            request.authenticated_userid
    }


################################################################################
# The login service.
################################################################################


def _get_couchdb_url(request):
    return request.registry.settings.tractdb_couchdb


service_login = cornice.Service(
    name='login',
    path='/login',
    description='TractDB Login',
    cors_origins=('*',),
    cors_credentials=True
)


@service_login.post()
def login_post(request):
    # Our JSON parameter, this could be validated
    json = request.json_body
    account = json['account']
    account_password = json['password']

    # Attempt to authenticate with CouchDB
    couchdb_response = requests.post(
        '{}/_session'.format(_get_couchdb_url(request)),
        data={
            'name': account,
            'password': account_password
        }
    )

    # If we succeeded, we can issue a cookie
    if couchdb_response.status_code == 200:
        # Get our authentication headers
        authentication_headers = pyramid.security.remember(
            request,
            account
        )

        # Include them in our response
        request.response.headerlist.extend(authentication_headers)

        # set expire date and add it to cookie
        cookie = request.response.headers['Set-Cookie']
        ticket = cookie[9:180]
        request.response.set_cookie(name='auth_tkt', value=ticket, max_age=86400, path='/', domain=None, secure=False,
                                    httponly=False, comment=None, expires=86400, overwrite=False)

    # Return the sames status code
    request.response.status_int = couchdb_response.status_code


################################################################################
# The logout service.
################################################################################


def acl_logout(request):
    return [
        (pyramid.security.Allow, pyramid.security.Authenticated, 'logout'),
        pyramid.security.DENY_ALL
    ]

service_logout = cornice.Service(
    name='logout',
    path='/logout',
    description='TractDB Logout',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_logout
)


@service_logout.post(permission='logout')
def logout_post(request):
    # TODO: probably need to check something?

    # Get our authentication headers
    authentication_headers = pyramid.security.forget(
        request
    )

    # Include them in our response
    request.response.headerlist.extend(authentication_headers)
