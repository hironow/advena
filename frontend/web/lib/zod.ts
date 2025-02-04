import { object, string } from 'zod';

export const signInSchema = object({
  idToken: string({ required_error: 'IdToken is required' }).min(1),
});
