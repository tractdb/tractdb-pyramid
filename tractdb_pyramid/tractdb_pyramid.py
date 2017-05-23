import pyramid.authentication
import pyramid.authorization
import pyramid.config
import pyramid.response
import pyramid.view
import yaml


def main(global_config, **settings):
    # Keys that start with secrets need to be loaded from file
    settings['secrets'] = {}
    secrets = [key_original for key_original in settings.keys() if key_original.startswith('secrets.')]
    for key_original in secrets:
        path = settings[key_original]
        key = key_original[len('secrets.'):]

        with open(settings[key_original]) as f:
            config = yaml.safe_load(f)
        settings['secrets'][key] = config

        del settings[key_original]

    # Configure our pyramid app
    config = pyramid.config.Configurator(settings=settings)

    # Authentication and Authorization
    pyramid_secret = settings['secrets']['pyramid']['authtktauthenticationpolicy_secret']
    policy_authentication = pyramid.authentication.AuthTktAuthenticationPolicy(
        pyramid_secret, hashalg='sha512'
    )
    policy_authorization = pyramid.authorization.ACLAuthorizationPolicy()

    config.set_authentication_policy(policy_authentication)
    config.set_authorization_policy(policy_authorization)

    # Sessions
    config.include('pyramid_beaker')

    # Application views
    config.include('cornice')
    config.scan('tractdb_pyramid.views')

    # Make the app
    app = config.make_wsgi_app()

    return app
