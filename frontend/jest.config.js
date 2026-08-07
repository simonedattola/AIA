/**
 * Jest config for AIA Legnano frontend (CRA/craco runner).
 * Merged via craco.config.js → jest.configure.
 */
module.exports = {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.js"],
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "^@/(.*)$": "<rootDir>/src/$1",
    // React Router v7 is ESM-first; Jest 27 (CRA) needs a CJS stub for component tests
    "^react-router-dom$": "<rootDir>/src/test-utils/react-router-dom-mock.js",
  },
  testMatch: [
    "<rootDir>/src/**/__tests__/**/*.{js,jsx}",
    "<rootDir>/src/**/*.{spec,test}.{js,jsx}",
  ],
  transformIgnorePatterns: [
    "[/\\\\]node_modules[/\\\\](?!(axios|lucide-react)/).+\\.(js|jsx|mjs)$",
  ],
};
