import { createContext, useContext, useState } from 'react';

const DirectBuyContext = createContext();

export const useDirectBuy = () => useContext(DirectBuyContext);

export function DirectBuyProvider({ children }) {
  const [directItem, setDirectItem] = useState(null);
  const clearDirectItem = () => setDirectItem(null);

  return (
    <DirectBuyContext.Provider value={{ directItem, setDirectItem, clearDirectItem }}>
      {children}
    </DirectBuyContext.Provider>
  );
}

export default DirectBuyContext;