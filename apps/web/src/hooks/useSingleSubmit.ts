import { useCallback, useRef } from 'react'

/**
 * Runs an action at most once until it settles.
 *
 * `isPending` from TanStack Query only flips on the NEXT render, so two clicks
 * landing in the same frame both sail through — which means two credits, or
 * worse, charging a client twice. This ref flips synchronously, so the second
 * click finds the door already closed.
 */
export function useSingleSubmit(): (task: () => Promise<unknown>) => void {
  const inFlight = useRef(false)

  return useCallback((task: () => Promise<unknown>) => {
    if (inFlight.current) return
    inFlight.current = true
    task()
      .catch(() => undefined) // the mutation's own onError already reports it
      .finally(() => {
        inFlight.current = false
      })
  }, [])
}
