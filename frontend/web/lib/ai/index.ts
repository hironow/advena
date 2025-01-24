import { vertex } from '@ai-sdk/google-vertex';
import { experimental_wrapLanguageModel as wrapLanguageModel } from 'ai';

import { customMiddleware } from './custom-middleware';

export const customModel = (apiIdentifier: string) => {
  return wrapLanguageModel({
    // TODO: build failure
    model: vertex(apiIdentifier),
    middleware: customMiddleware,
  });
};
