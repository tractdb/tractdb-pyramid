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
    return request.registry.settings['tractdb_couchdb']


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
        # Store the CouchDB cookies for communicating with CouchDB from this session
        request.session['couchdb_cookies'] = couchdb_response.cookies

        # TODO: until we can handle sessions in our server objects
        request.session['temp_couchdb_user'] = account
        request.session['temp_couchdb_user_password'] = account_password

        # Provide authentication headers in our response
        authentication_headers = pyramid.security.remember(
            request,
            account
        )
        request.response.headerlist.extend(authentication_headers)

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
