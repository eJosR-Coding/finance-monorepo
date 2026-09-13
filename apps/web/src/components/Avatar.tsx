/** Flat initials tile. No photo uploads anywhere in this product. */

interface AvatarProps {
  initials: string
  size?: number
  tone?: 'neutral' | 'accent' | 'dark'
}

const BACKGROUNDS = {
  neutral: { background: 'var(--color-neutral-200)', color: 'var(--color-ink)' },
  accent: { background: 'var(--color-accent-700)', color: '#fff' },
  dark: { background: 'var(--color-neutral-800)', color: '#fff' },
}

export function Avatar({ initials, size = 26, tone = 'neutral' }: AvatarProps) {
  return (
    <div
      className="avatar"
      style={{ width: size, height: size, fontSize: size * 0.4, ...BACKGROUNDS[tone] }}
      aria-hidden="true"
    >
      {initials}
    </div>
  )
}
