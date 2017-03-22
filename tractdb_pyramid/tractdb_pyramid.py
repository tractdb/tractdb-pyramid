import pyramid.authentication
import pyramid.authorization
import pyramid.config
import pyramid.response
import pyramid.view
import yaml


def main(global_config, **settings):
    # Parse our couchdb secrets
    with open(settings['tractdb_couchdb_secrets']) as f:
        config = yaml.safe_load(f)
    settings['tractdb_couchdb_secrets'] = config

    # Configure our pyramid app
    config = pyramid.config.Configurator(settings=settings)

    pyramid_secret = settings['tractdb_pyramid_secrets']['pyramid_secret']

    # Authentication and Authorization
    policy_authentication = pyramid.authentication.AuthTktAuthenticationPolicy(
        pyramid_secret, hashalg='sha512'
    )
    policy_authorization = pyramid.authorization.ACLAuthorizationPolicy()

    config.set_authentication_policy(policy_authentication)
    config.set_authorization_policy(policy_authorization)

    # Application views
    config.include('cornice')
    config.scan('tractdb_pyramid.views')

    # Make the app
    app = config.make_wsgi_app()

    return app
