import { missingExport } from "./missing-module";

type User = {
  id: number;
  name: string;
};

const user: User = {
  id: "not-a-number",
};

function renderUser(user: User, mode: "short" | "long") {
  return user.email.toLowerCase() + mode;
}

renderUser(user);
render_user(user, "short");
console.log(neverDeclared);

