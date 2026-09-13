/**
 * i18n setup. Spanish is the product language; English is there so the app is
 * genuinely translatable and not just hardcoded strings wearing a t() costume.
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import { es } from '@/lib/locales/es'
import { en } from '@/lib/locales/en'

export const SUPPORTED_LANGUAGES = ['es', 'en'] as const
export type Language = (typeof SUPPORTED_LANGUAGES)[number]

const STORAGE_KEY = 'prestameami.language'

function initialLanguage(): Language {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored !== null && (SUPPORTED_LANGUAGES as readonly string[]).includes(stored)) {
    return stored as Language
  }
  return navigator.language.startsWith('en') ? 'en' : 'es'
}

void i18n.use(initReactI18next).init({
  resources: {
    es: { translation: es },
    en: { translation: en },
  },
  lng: initialLanguage(),
  fallbackLng: 'es',
  interpolation: { escapeValue: false },
})

export function changeLanguage(language: Language): void {
  localStorage.setItem(STORAGE_KEY, language)
  void i18n.changeLanguage(language)
}

export default i18n
