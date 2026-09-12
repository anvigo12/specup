// UNIT-AUTH-0031. The name is load-bearing: test-file-naming-convention strips the `.test`
// marker and looks for `certificate_validator.ts` inside the perimeter, which is how the
// `tests` edge is recomputed rather than asserted.
import { validateCertificate } from "./certificate_validator";

test("an empty certificate is rejected", () => {
  expect(validateCertificate("")).toBe(false);
});
