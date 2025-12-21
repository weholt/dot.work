// Flat config for ESLint 9+
import js from "@eslint/js";
import stylistic from "eslint-config-prettier";
import importPlugin from "eslint-plugin-import";
import n from "eslint-plugin-n";
import promise from "eslint-plugin-promise";
import unicorn from "eslint-plugin-unicorn";

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  { ignores: ["dist/", "node_modules/"] },
  js.configs.recommended,
  stylistic,
  {
    files: ["**/*.ts", "**/*.tsx"],
    languageOptions: {
      parser: await import("@typescript-eslint/parser"),
      parserOptions: { project: false, ecmaVersion: "latest", sourceType: "module" }
    },
    plugins: {
      "@typescript-eslint": await import("@typescript-eslint/eslint-plugin"),
      import: importPlugin,
      n,
      promise,
      unicorn
    },
    rules: {
      "no-console": "warn",
      "import/order": ["error", { "newlines-between": "always", "alphabetize": { "order": "asc" } }],
      "unicorn/prefer-node-protocol": "error",
      "n/no-unsupported-features/es-syntax": "off",
      "@typescript-eslint/consistent-type-imports": "error"
    }
  }
];
