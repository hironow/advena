// Define your models here.

export interface Model {
  id: string;
  label: string;
  apiIdentifier: string;
  description: string;
}

export const models: Array<Model> = [
  {
    id: 'gemini-2.0-flash-exp',
    label: 'gemini-2.0-flash-exp',
    apiIdentifier: 'gemini-2.0-flash-exp',
    description: 'gemini-2.0-flash-exp model.',
  },
] as const;

export const DEFAULT_MODEL_NAME: string = 'gemini-2.0-flash-exp';
