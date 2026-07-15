import { createContext, useContext, useEffect, useState } from "react";
import { fetchSettings, fetchNav } from "./api";

const SiteContext = createContext({ settings: null, nav: [], loading: true });

export function SiteProvider({ children }) {
  const [settings, setSettings] = useState(null);
  const [nav, setNav] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchSettings().catch(() => null), fetchNav().catch(() => [])]).then(([s, n]) => {
      setSettings(s);
      setNav(n);
      setLoading(false);
    });
  }, []);

  return (
    <SiteContext.Provider value={{ settings, nav, loading }}>
      {children}
    </SiteContext.Provider>
  );
}

export const useSite = () => useContext(SiteContext);
