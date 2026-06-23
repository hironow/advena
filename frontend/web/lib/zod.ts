import { z } from "zod";

export const signInSchema = z.object({
  idToken: z.string().min(1, "IdToken is required"),
});
