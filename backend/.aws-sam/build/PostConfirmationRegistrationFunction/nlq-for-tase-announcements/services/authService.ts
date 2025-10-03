import { CognitoIdentityProviderClient, SignUpCommand, ConfirmSignUpCommand, ResendConfirmationCodeCommand } from '@aws-sdk/client-cognito-identity-provider';

const REGION = import.meta.env.VITE_COGNITO_REGION;
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID;

if (!REGION) {
  console.warn('VITE_COGNITO_REGION is not defined; registration will fail.');
}

if (!CLIENT_ID) {
  console.warn('VITE_COGNITO_CLIENT_ID is not defined; registration will fail.');
}

const client = new CognitoIdentityProviderClient({ region: REGION });

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

export async function signUpWithCognito(payload: SignUpPayload) {
  ensureConfig();

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

  return client.send(command);
}

export async function confirmSignUp(email: string, confirmationCode: string) {
  ensureConfig();

  const command = new ConfirmSignUpCommand({
    ClientId: CLIENT_ID!,
    Username: email,
    ConfirmationCode: confirmationCode,
  });

  return client.send(command);
}

export async function resendConfirmationCode(email: string) {
  ensureConfig();

  const command = new ResendConfirmationCodeCommand({
    ClientId: CLIENT_ID!,
    Username: email,
  });

  return client.send(command);
}