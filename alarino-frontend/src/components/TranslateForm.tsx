import React, { useState } from 'react'
import axios from 'axios'

import {
  FormControl,
  FormLabel,
  Input,
  Select,
  Button,
  VStack,
  useToast
} from '@chakra-ui/react'

interface TranslateFormProps {
  onTranslation: (translatedText: string) => void
}

const TranslateForm: React.FC<TranslateFormProps> = ({ onTranslation }) => {
  const [inputText, setInputText] = useState('')
  const [sourceLanguage, setSourceLanguage] = useState('en')
  const [targetLanguage, setTargetLanguage] = useState('yo')
  const toast = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const response = await axios.post('/api/translate', {
        text: inputText,
        source_lang: sourceLanguage,
        target_lang: targetLanguage
      })

      const data = response.data
      onTranslation(data.translation)
    } catch (error) {
      console.error('Error calling translation API:', error)
      onTranslation('Error translating text.')
      toast({
        title: 'Translation Error',
        description: 'Could not translate. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <VStack align="stretch">
        <FormControl>
          <FormLabel htmlFor="inputText">Text to translate:</FormLabel>
          <Input
            id="inputText"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Enter your text here"
          />
        </FormControl>

        <FormControl>
          <FormLabel htmlFor="sourceLang">Source Language:</FormLabel>
          <Select
            id="sourceLang"
            value={sourceLanguage}
            onChange={(e) => setSourceLanguage(e.target.value)}
          >
            <option value="en">English</option>
            <option value="yo">Yoruba</option>
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel htmlFor="targetLang">Target Language:</FormLabel>
          <Select
            id="targetLang"
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
          >
            <option value="en">English</option>
            <option value="yo">Yoruba</option>
          </Select>
        </FormControl>

        <Button colorScheme="blue" type="submit">
          Translate
        </Button>
      </VStack>
    </form>
  )
}

export default TranslateForm
