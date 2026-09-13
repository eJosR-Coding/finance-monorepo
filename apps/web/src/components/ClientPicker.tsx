/** Search-as-you-type client selector for the new-credit form. */

import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Avatar } from '@/components/Avatar'
import { StatusTag } from '@/components/Tag'
import { useClients } from '@/hooks/queries'
import type { ClientListItem } from '@/types/api'

interface ClientPickerProps {
  selected: ClientListItem | null
  onSelect: (client: ClientListItem | null) => void
  invalid?: boolean
}

export function ClientPicker({ selected, onSelect, invalid = false }: ClientPickerProps) {
  const { t } = useTranslation()
  const [term, setTerm] = useState('')
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const { data } = useClients({ search: term })
  const options = data?.items ?? []

  useEffect(() => {
    const onClickOutside = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const label = selected === null ? term : `${selected.full_name} — DNI ${selected.dni}`

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <input
        className={invalid ? 'input input-invalid' : 'input'}
        placeholder={t('newCredit.clientPlaceholder')}
        value={label}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setTerm(event.target.value)
          onSelect(null)
          setOpen(true)
        }}
        role="combobox"
        aria-expanded={open}
        aria-controls="client-options"
        autoComplete="off"
      />

      {open && options.length > 0 && (
        <ul
          id="client-options"
          role="listbox"
          style={{
            position: 'absolute',
            zIndex: 20,
            top: '100%',
            left: 0,
            right: 0,
            margin: 0,
            padding: 0,
            listStyle: 'none',
            background: 'var(--color-bg)',
            border: '1px solid var(--divider)',
            maxHeight: 260,
            overflowY: 'auto',
            boxShadow: 'var(--shadow-raised)',
          }}
        >
          {options.map((option) => (
            <li key={option.id}>
              <button
                type="button"
                role="option"
                aria-selected={selected?.id === option.id}
                onClick={() => {
                  onSelect(option)
                  setTerm('')
                  setOpen(false)
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  width: '100%',
                  padding: '8px 10px',
                  background: 'transparent',
                  border: 0,
                  borderBottom: '1px solid var(--divider)',
                  cursor: 'pointer',
                  font: 'inherit',
                  fontSize: 13.5,
                  textAlign: 'left',
                }}
              >
                <Avatar initials={option.initials} />
                <span style={{ flex: 1 }}>{option.full_name}</span>
                <span className="muted" style={{ fontSize: 12 }}>
                  {option.dni}
                </span>
                <StatusTag status={option.credit_status} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
