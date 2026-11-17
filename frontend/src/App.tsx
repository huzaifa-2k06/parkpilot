import { useQuery } from '@tanstack/react-query'
import { lazy, Suspense, useEffect, useState } from 'react'
import { getEvents, getSpaces, getStatus } from './api/parking'
import { EventList } from './components/Events'
import { Icon } from './components/Icon'
import { LiveLot } from './pages/LiveLot'
import { Simulate } from './pages/Simulate'

const sections = [
  { id: 'lot', title: 'Live lot', icon: 'lot' },
  { id: 'simulate', title: 'Simulate', icon: 'simulate' },
  { id: 'insights', title: 'Insights', icon: 'insights' },
  { id: 'events', title: 'Events', icon: 'events' },
] as const
const refreshInterval = 1500
const Insights = lazy(async () => ({ default: (await import('./pages/Insights')).Insights }))

function selectedSection() {
  return sections.find(section => `#${section.id}` === window.location.hash) ?? sections[0]
}

export function App() {
  const [section, setSection] = useState(selectedSection)
  useEffect(() => {
    const select = () => setSection(selectedSection())
    window.addEventListener('hashchange', select)
    return () => window.removeEventListener('hashchange', select)
  }, [])

  const spaces = useQuery({
    queryKey: ['spaces'],
    queryFn: ({ signal }) => getSpaces(signal),
    refetchInterval: refreshInterval,
  })
  const events = useQuery({
    queryKey: ['events'],
    queryFn: ({ signal }) => getEvents(signal),
    refetchInterval: refreshInterval,
  })
  const status = useQuery({
    queryKey: ['simulation'],
    queryFn: ({ signal }) => getStatus(signal),
    refetchInterval: refreshInterval,
  })

  const issue = spaces.error ?? events.error ?? status.error
  return (
    <div className="workspace-shell">
      <a className="skip-link" href="#dashboard-main" onClick={event => {
        event.preventDefault()
        document.getElementById('dashboard-main')?.focus()
      }}>Skip to dashboard</a>
      <aside className="nav-rail">
        <a className="brand-mark" href="#lot" aria-label="ParkPilot home"><Icon name="logo" size={27} /></a>
        <nav aria-label="Main navigation">
          {sections.map(item => <a className="nav-item" key={item.id} href={`#${item.id}`}
            aria-current={section.id === item.id ? 'page' : undefined}>
            <span><Icon name={item.icon} /></span>
            <span>{item.title}</span>
          </a>)}
        </nav>
        <span className="nav-local" title="Simulated parking facility">Demo</span>
      </aside>
      <main id="dashboard-main" className="workspace-main" tabIndex={-1}>
        <header className="workspace-heading">
          <div>
            <a className="wordmark" href="#lot">ParkPilot</a>
            <h1>{section.title}</h1>
          </div>
          <div className="status-cluster">
            <span className={`status-pill${status.data?.running && !issue ? ' enabled' : ''}`}>
              <Icon name={status.data?.running ? 'play' : 'pause'} size={15} />
              {status.data && !status.isError
                ? status.data.running ? 'Simulation enabled' : 'Simulation paused'
                : status.isError ? 'Simulation unavailable' : 'Checking simulation…'}
            </span>
            <span className="sync-time"><Icon name="clock" size={14} />
              {spaces.dataUpdatedAt
                ? <>Updated <time dateTime={new Date(spaces.dataUpdatedAt).toISOString()}>
                  {new Date(spaces.dataUpdatedAt).toLocaleTimeString([], {
                    hour: '2-digit', minute: '2-digit', second: '2-digit',
                  })}
                </time></>
                : 'Waiting for lot data'}
            </span>
          </div>
        </header>
        {issue && <div className="status-banner" role="status">
          <Icon name="alert" size={19} />
          <span>{issue.message}{spaces.data ? ' Showing the last loaded lot state.' : ''}</span>
          <button className="text-button" type="button" onClick={() => {
            void spaces.refetch()
            void events.refetch()
            void status.refetch()
          }}><Icon name="refresh" size={16} /> Retry</button>
        </div>}

        {section.id === 'lot' && <LiveLot spaces={spaces.data} events={events.data} />}
        {section.id === 'simulate' && <Simulate spaces={spaces.data} events={events.data}
          running={status.isError ? undefined : status.data?.running} />}
        {section.id === 'insights' && <Suspense fallback={<p className="quiet-state" role="status">Loading insights…</p>}>
          <Insights />
        </Suspense>}
        {section.id === 'events' && <section className="card event-history" aria-label="Recorded events">
          <div className="card-header">
            <div><h2>Event history</h2><p>Latest 50 accepted events from the simulated lot</p></div>
          </div>
          <EventList events={events.data} filterable accepted />
        </section>}
      </main>
    </div>
  )
}
