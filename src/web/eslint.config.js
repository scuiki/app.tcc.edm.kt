import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'src/http/schema.d.ts']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    plugins: { react },
    settings: { react: { version: '19.2' } },
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      // Componente definido dentro de outro nasce de novo a cada render e perde o estado
      'react/no-unstable-nested-components': 'error',
      'react/jsx-key': 'error',
      // A lista de dependências é consequência do código, nunca se silencia
      'react-hooks/exhaustive-deps': 'error',
    },
  },
])
