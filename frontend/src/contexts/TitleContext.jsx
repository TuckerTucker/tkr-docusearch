/**
 * TitleContext
 *
 * Provides page title and header content state that can be set by child routes
 * and consumed by the Layout/Header
 */
import { createContext, useContext, useState } from 'react';

const TitleContext = createContext();

export function TitleProvider({ children }) {
  const [title, setTitle] = useState('Document Library');
  const [isLoading, setIsLoading] = useState(false);
  const [headerContent, setHeaderContent] = useState(null);

  return (
    <TitleContext.Provider value={{ title, setTitle, isLoading, setIsLoading, headerContent, setHeaderContent }}>
      {children}
    </TitleContext.Provider>
  );
}

export function useTitle() {
  const context = useContext(TitleContext);
  if (!context) {
    throw new Error('useTitle must be used within TitleProvider');
  }
  return context;
}
