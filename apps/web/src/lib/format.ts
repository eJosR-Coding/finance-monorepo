/**
 * Display formatting. Every amount the API sends is a decimal STRING, so we
 * format the text and never parse it into a float - that's how precision dips.
 */

const MONEY_SYMBOL = 'S/'

/** "1284.5" -> "S/ 1,284.50". Grouping is done on the string, digit by digit. */
export function formatMoney(value: string | null | undefined, symbol = MONEY_SYMBOL): string {
  if (value === null || value === undefined || value === '') return `${symbol} 0.00`
  const negative = value.startsWith('-')
  const clean = negative ? value.slice(1) : value
  const [whole = '0', decimals = ''] = clean.split('.')
  const padded = (decimals + '00').slice(0, 2)
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return `${negative ? '-' : ''}${symbol} ${grouped}.${padded}`
}

/** Same as above without the symbol, for inputs and tight table cells. */
export function formatAmount(value: string | null | undefined): string {
  return formatMoney(value, '').trim()
}

/** "0.6563965" -> "0.6563965 %". `decimals` trims or pads the tail. */
export function formatPercent(value: string | null | undefined, decimals?: number): string {
  if (value === null || value === undefined || value === '') return '0 %'
  if (decimals === undefined) return `${value} %`
  const parsed = Number(value)
  return `${parsed.toFixed(decimals)} %`
}

/** "2026-09-19" -> "19/09/2026". Parsed by hand to dodge timezone shifts. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const [datePart = ''] = value.split('T')
  const [year, month, day] = datePart.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

export function toIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function todayIso(): string {
  return toIsoDate(new Date())
}

/** Day difference between two ISO dates, positive when `a` is later. */
export function daysBetween(a: string, b: string): number {
  const millis = Date.parse(`${a}T00:00:00`) - Date.parse(`${b}T00:00:00`)
  return Math.round(millis / 86_400_000)
}

export function initialsOf(name: string): string {
  const [first = '', second = ''] = name.trim().split(/\s+/)
  return `${first.charAt(0)}${second.charAt(0)}`.toUpperCase()
}
