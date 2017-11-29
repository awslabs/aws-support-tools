var https = require('https');
var jose = require('node-jose');

var region = 'ap-southeast-2';
var userpool_id = 'ap-southeast-2_xxxxxxxxx';
var keys_url = 'https://cognito-idp.' + region + '.amazonaws.com/' + userpool_id + '/.well-known/jwks.json';

exports.handler = (event, context, callback) => {
    var token = event['token'];
    var sections = token.split('.');
    // get the kid from the headers prior to verification
    var header = jose.util.base64url.decode(sections[0]);
    header = JSON.parse(header);
    var kid = header['kid'];
    // download the public keys
    https.get(keys_url, function(response) {
        if (response.statusCode == 200) {
            response.on('data', function(body) {
                var keys = JSON.parse(body)['keys'];
                // search for the kid in the downloaded public keys
                var key_index = -1;
                for (var i=0; i < keys.length; i++) {
                        if (kid == keys[i].kid) {
                            key_index = i;
                            break;
                        }
                }
                if (key_index == -1) {
                    callback('Public key not found in jwks.json');
                }
                // construct the public key
                jose.JWK.asKey(keys[key_index]).
                then(function(result) {
                    // verify the signature
                    jose.JWS.createVerify(result).
                    verify(token).
                    then(function(result) {
                        // do some stuff with our claims
                        callback(null, JSON.parse(result.payload));
                    }).
                    catch(function() {
                        callback('Signature verification failed');
                    });
                });
            });
        }
    });
}