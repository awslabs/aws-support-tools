const _ = require('lodash');
const Axios = require('axios');
const jose = require('jose');

// Input validations
const input = ['COGNITO_POOL_ID', 'COGNITO_REGION', 'COGNITO_CLIENT_ID'];
for (const variable of input) {
    if (!process.env.hasOwnProperty(variable) || process.env[variable].length === 0) {
        throw new Error(`Environment variable is required for ${variable}.`);
    }
}

// Global variables declaration
const cognitoClientId = process.env.COGNITO_CLIENT_ID;
const cognitoIssuer = `https://cognito-idp.${process.env.COGNITO_REGION}.amazonaws.com/${process.env.COGNITO_POOL_ID}`;
let keyStore;

const extractToken = async (event) => {
    const authorization = _.get(event, ['headers', 'Authorization'], '');
    if (authorization === '') return authorization;
    return authorization.split(' ')[1];  // Cut 'Bearer' out
};

const getPublicKeys = async () => {
    const url = `${cognitoIssuer}/.well-known/jwks.json`;
    const res = await Axios.default.get(url);
    return res.data;
};

const getPublicKeysIfNotCached = async (keyStore) => {
    if (!keyStore) {
        const keys = await getPublicKeys();
        keyStore = new jose.JWKS.asKeyStore(keys);
    }
    return keyStore;
};

const verifyIdToken = async (token, keyStore, issuer, audience) => {
    return jose.JWT.IdToken.verify(
        token,
        keyStore,
        {
            issuer,
            audience,
            algorithms: ['RS256']
        }
    );
};

const isAuthorized = async (decryptedToken) => {
    // Add authorization logic here
    return true;
};

const redirectTo = async (decryptedToken) => {
    // Add redirection logic here
    return 'redirectPath';
};

module.exports.handler = async (event) => {
    console.log('event', JSON.stringify(event));
    let decryptedToken;
    try {
        const token = await extractToken(event);
        keyStore = await getPublicKeysIfNotCached(keyStore);
        decryptedToken = await verifyIdToken(token, keyStore, cognitoIssuer, cognitoClientId);
        console.log('decryptedToken', JSON.stringify(decryptedToken));
    } catch (e) {
        console.error(e);
        return {statusCode: 401, body: 'Unauthorized'};
    }
    try {
        const authorized = await isAuthorized(decryptedToken);
        if (authorized) {
            return {statusCode: 302, headers: {Location: '/' + await redirectTo(decryptedToken)}};
        }
        return {statusCode: 403, body: 'Forbidden'};
    } catch (e) {
        console.error(e);
        return {statusCode: 403, body: 'Forbidden'};
    }
};
