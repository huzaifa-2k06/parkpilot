import type { ReactNode } from 'react'

const paths: Record<string, ReactNode> = {
  logo: <><path d="M7 20V4h6a4.5 4.5 0 0 1 0 9H7"/><path d="m14 18 2.5 2.5L21 16"/></>,
  lot: <><rect x="3.5" y="3.5" width="17" height="17" rx="4"/><path d="M9 16.5v-9h3.5a2.5 2.5 0 0 1 0 5H9"/></>,
  simulate: <><path d="M7 7h12m-4-4 4 4-4 4m2 6H5m4-4-4 4 4 4"/></>,
  insights: <><path d="M4 4v15h16M8 14l4-4 3 2 5-6"/></>,
  events: <><path d="M7 6h13M7 12h13M7 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/></>,
  arrowRight: <path d="M4 12h15m-6-6 6 6-6 6"/>,
  arrowIn: <path d="M4 8h8a5 5 0 0 1 5 5v6m-4-4 4 4 4-4"/>,
  arrowOut: <path d="M5 18v-6a5 5 0 0 1 5-5h9m-4-4 4 4-4 4"/>,
  car: <><path d="m4 11 2-5h12l2 5m-16 0h16l1 2v4H3v-4zM5 17v2m14-2v2M6 14h2m8 0h2"/></>,
  clock: <><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v5l3 1.5"/></>,
  play: <path d="m8 5 11 7-11 7z"/>,
  pause: <path d="M9 5v14m6-14v14"/>,
  alert: <><circle cx="12" cy="12" r="8.5"/><path d="M12 7v6m0 3h.01"/></>,
  refresh: <><path d="M20 10a8 8 0 1 0-2 8m2-13v5h-5"/></>,
}

export function Icon({ name, size = 20 }: { name: keyof typeof paths; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  )
}
