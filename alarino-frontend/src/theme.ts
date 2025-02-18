import { extendTheme, ThemeConfig } from '@chakra-ui/react'

const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: true,
}

const customTheme = extendTheme({
  config,
  // example overrides
  // colors: {
  //   brand: {
  //     50: '#e3fafc',
  //     100: '#c5f6fa',
  //     200: '#99e9f2',
  //     300: '#66d9e8',
  //     400: '#3bc9db',
  //     500: '#22b8cf', // brand.500
  //     600: '#15aabf',
  //     700: '#1098ad',
  //     800: '#0c8599',
  //     900: '#0b7285',
  //   },
  // },
  fonts: {
    heading: `'Open Sans', sans-serif`,
    body: `'Roboto', sans-serif`,
  },
})

export default customTheme
