import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import Dashboard from './pages/Dashboard'
import TicketList from './pages/TicketList'
import TicketDetail from './pages/TicketDetail'
import NetworkOps from './pages/NetworkOps'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/tickets" element={<TicketList />} />
          <Route path="/tickets/:id" element={<TicketDetail />} />
          <Route path="/network-ops" element={<NetworkOps />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

