const React = require("react");

function Link({ children, to, ...rest }) {
  return React.createElement("a", { href: to, ...rest }, children);
}

function NavLink({ children, to, ...rest }) {
  return React.createElement("a", { href: to, ...rest }, children);
}

function useLocation() {
  return { pathname: "/" };
}

module.exports = {
  Link,
  NavLink,
  useLocation,
  MemoryRouter: ({ children }) => React.createElement(React.Fragment, null, children),
  BrowserRouter: ({ children }) => React.createElement(React.Fragment, null, children),
};
