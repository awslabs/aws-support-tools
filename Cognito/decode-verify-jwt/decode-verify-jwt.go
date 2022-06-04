package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"os"

	"github.com/golang-jwt/jwt/v4"
	"github.com/lestrrat/go-jwx/jwk"
)

var region string
var userpool_id string
var app_client_id string
var keys_url string

var keys *jwk.Set

type AWSCognitoClaims struct {
	ClientId string `json:client_id`
	Username string `json:username`
	jwt.StandardClaims
}

func init() {

	region = os.Getenv("AWS_REGION")
	userpool_id = os.Getenv("USERPOOL_ID")
	app_client_id = os.Getenv("APP_CLIENT_ID")
	keys_url = fmt.Sprintf("https://cognito-idp.%v.amazonaws.com/%v/.well-known/jwks.json", region, userpool_id)

	var err error
	keys, err = jwk.FetchHTTP(keys_url)
	if err != nil {
		log.Fatal(err)
	}
}

func HandleRequest(ctx context.Context, event map[string]string) (jwt.Claims, error) {

	token_string := event["token"]
	claims := &AWSCognitoClaims{}

	// Parse and validate received token
	_, err := jwt.ParseWithClaims(token_string, claims, validateToken)
	if err != nil {
		return nil, err
	}

	return claims, nil
}

func validateToken(token *jwt.Token) (interface{}, error) {

	// get the kid from the headers prior to verification
	keyID, ok := token.Header["kid"].(string)
	if !ok {
		return nil, errors.New("expecting JWT header to have string kid")
	}

	//  search for the kid in the downloaded public keys
	if key := keys.LookupKeyID(keyID); len(key) == 1 {

		claims := token.Claims.(*AWSCognitoClaims)
		// verify the Audience (use claims.ClientId if verifying an access token)
		if claims.Audience != app_client_id {
			return nil, errors.New("token was not issued for this audience")
		}

		// construct the public key
		return key[0].Materialize()

	}

	return nil, fmt.Errorf("unable to find key %q", keyID)
}

func main() {
	event := make(map[string]string)

	// for testing locally you can enter the JWT ID Token here
	event["token"] = ""

	HandleRequest(context.Background(), event)
	// lambda.Start(HandleRequest)
}
