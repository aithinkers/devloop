# Single Sign-On
We use Okta as the identity provider. Protocol is SAML 2.0 for the web app and OIDC for the
mobile app. User provisioning is via SCIM. Group claims drive role mapping. Prod and staging
have separate Okta apps.
