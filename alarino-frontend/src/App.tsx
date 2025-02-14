// src/App.tsx

import React, { useState } from 'react'
import { Container, Heading, Box, Text } from '@chakra-ui/react'
import TranslateForm from './components/TranslateForm'

function App() {
  const [translationResult, setTranslationResult] = useState('')

  const handleTranslation = (translatedText: string) => {
    setTranslationResult(translatedText)
  }

  return (
    <Container maxW="md" py={8}>
      <Heading as="h1" mb={6}>
        Alarino: English ↔ Yoruba Translation
      </Heading>

      <TranslateForm onTranslation={handleTranslation} />

      {translationResult && (
        <Box mt={8} p={4} borderWidth="1px" borderRadius="md">
          <Heading as="h2" size="md" mb={2}>
            Translated Text
          </Heading>
          <Text>{translationResult}</Text>
        </Box>
      )}
    </Container>
  )
}

export default App
