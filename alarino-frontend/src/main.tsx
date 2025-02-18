import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ChakraProvider } from '@chakra-ui/react'
import customTheme from './theme'


import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ChakraProvider theme={customTheme}>
      <App />
    </ChakraProvider>
  </StrictMode>,
)
