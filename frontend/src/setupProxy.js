/**
 * Dev proxy: with REACT_APP_BACKEND_URL empty, the SPA calls `/api/*` on the
 * same origin. Forward those (and uploads/docs) to the FastAPI backend.
 */
const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function setupProxy(app) {
  const target = process.env.BACKEND_PROXY_TARGET || "http://127.0.0.1:8000";
  const opts = {
    target,
    changeOrigin: true,
    logLevel: "silent",
  };
  app.use("/api", createProxyMiddleware(opts));
  app.use("/docs", createProxyMiddleware(opts));
  app.use("/redoc", createProxyMiddleware(opts));
  app.use("/openapi.json", createProxyMiddleware(opts));
  app.use("/metrics", createProxyMiddleware(opts));
};
