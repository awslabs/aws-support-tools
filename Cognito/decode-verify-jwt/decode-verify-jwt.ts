import { CognitoJwtVerifier } from "aws-jwt-verify";

const userPoolId = process.env.USER_POOL_ID as string;
if (!userPoolId) {
  throw new Error("env var required: USER_POOL_ID");
}
const clientId = process.env.CLIENT_ID as string;
if (!clientId) {
  throw new Error("env var required: CLIENT_ID");
}

const verifier = CognitoJwtVerifier.create({
  userPoolId,
  clientId,
  tokenUse: "access", // or set to "id" if you want to verify ID tokens
});

const handler = async (
  request: ClaimVerifyRequest
): Promise<ClaimVerifyResult> => {
  let result: ClaimVerifyResult;
  try {
    console.log(`user claim verify invoked for ${JSON.stringify(request)}`);
    const payload = await verifier.verify(request.token as string);
    console.log(`payload confirmed for ${payload.username}`);
    result = {
      userName: payload.username,
      clientId: payload.client_id,
      isValid: true,
    };
  } catch (error) {
    result = { userName: "", clientId: "", error, isValid: false };
  }
  return result;
};

export { handler };

// Helper types:
export interface ClaimVerifyRequest {
  readonly token?: string;
}

export interface ClaimVerifyResult {
  readonly userName: string;
  readonly clientId: string;
  readonly isValid: boolean;
  readonly error?: any;
}
