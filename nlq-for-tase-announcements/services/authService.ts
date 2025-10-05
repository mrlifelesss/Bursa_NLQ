import {
  CognitoIdentityProviderClient,
  SignUpCommand,
  ConfirmSignUpCommand,
  ResendConfirmationCodeCommand,
  InitiateAuthCommand,
} from '@aws-sdk/client-cognito-identity-provider';

const REGION = import.meta.env.VITE_COGNITO_REGION;
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID;

if (!REGION) {
  console.warn('VITE_COGNITO_REGION is not defined; registration will fail.');
}

if (!CLIENT_ID) {
  console.warn('VITE_COGNITO_CLIENT_ID is not defined; registration will fail.');
}

let client: CognitoIdentityProviderClient | null = null;

export interface SignUpPayload {
  email: string;
  password: string;
  name?: string;
}

function ensureConfig() {
  if (!REGION || !CLIENT_ID) {
    throw new Error('Cognito configuration missing. Please set VITE_COGNITO_REGION and VITE_COGNITO_CLIENT_ID.');
  }
}

function getClient() {
  ensureConfig();
  if (!client) {
    client = new CognitoIdentityProviderClient({ region: REGION });
  }
  return client;
}

export async function signUpWithCognito(payload: SignUpPayload) {
  const cognito = getClient();

  const command = new SignUpCommand({
    ClientId: CLIENT_ID!,
    Username: payload.email,
    Password: payload.password,
    UserAttributes: payload.name
      ? [
          { Name: 'email', Value: payload.email },
          { Name: 'name', Value: payload.name },
        ]
      : [{ Name: 'email', Value: payload.email }],
  });

  return cognito.send(command);
}

export async function confirmSignUp(email: string, confirmationCode: string) {
  const cognito = getClient();

  const command = new ConfirmSignUpCommand({
    ClientId: CLIENT_ID!,
    Username: email,
    ConfirmationCode: confirmationCode,
  });

  return cognito.send(command);
}

export async function resendConfirmationCode(email: string) {
  const cognito = getClient();

  const command = new ResendConfirmationCodeCommand({
    ClientId: CLIENT_ID!,
    Username: email,
  });

  return cognito.send(command);
}

export interface SignInPayload {
  email: string;
  password: string;
}

export interface SignInTokens {
  accessToken: string;
  idToken: string;
  refreshToken?: string;
  expiresIn?: number;
  tokenType?: string;
}

export async function signInWithCognito(payload: SignInPayload): Promise<SignInTokens> {
  const cognito = getClient();

  const command = new InitiateAuthCommand({
    AuthFlow: 'USER_PASSWORD_AUTH',
    ClientId: CLIENT_ID!,
    AuthParameters: {
      USERNAME: payload.email,
      PASSWORD: payload.password,
    },
  });

  const response = await cognito.send(command);

  if (response.ChallengeName) {
    throw new Error('Additional authentication is required to sign in.');
  }

  const result = response.AuthenticationResult;

  if (!result || !result.AccessToken || !result.IdToken) {
    throw new Error('Authentication failed. Please try again.');
  }

  return {
    accessToken: result.AccessToken,
    idToken: result.IdToken,
    refreshToken: result.RefreshToken ?? undefined,
    expiresIn: result.ExpiresIn ?? undefined,
    tokenType: result.TokenType ?? undefined,
  };
}
