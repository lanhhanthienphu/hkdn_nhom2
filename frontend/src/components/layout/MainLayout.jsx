import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#f8f9ff]">
      <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="md:pl-64">
        <Header onMenuToggle={() => setSidebarOpen(true)} />
        <main className="relative pt-16 bg-[#f8f9ff] min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

