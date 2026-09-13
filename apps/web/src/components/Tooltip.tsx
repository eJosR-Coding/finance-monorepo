/** The small "?" glyph next to TEA / TCEA / late-rate labels. */

export function Tooltip({ text }: { text: string }) {
  return (
    <span
      title={text}
      tabIndex={0}
      role="note"
      aria-label={text}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 14,
        height: 14,
        borderRadius: '50%',
        border: '1px solid currentColor',
        fontSize: 10,
        opacity: 0.55,
        cursor: 'help',
        marginLeft: 5,
        verticalAlign: 'middle',
      }}
    >
      ?
    </span>
  )
}
