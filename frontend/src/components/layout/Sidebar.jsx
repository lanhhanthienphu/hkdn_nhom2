import { NavLink, useLocation } from 'react-router-dom'
import { useState } from 'react'

const navSections = [
  {
    label: 'TỔNG QUAN',
    items: [
      { path: '/dashboard', icon: 'dashboard', label: 'Dashboard Quản trị' },
      { path: '/network-ops', icon: 'router', label: 'Network Ops Center' },
    ],
  },
  {
    label: 'YÊU CẦU SỰ CỐ',
    items: [
      { path: '/tickets/new', icon: 'add_circle', label: 'Gửi yêu cầu mới' },
      { path: '/my-tickets', icon: 'receipt_long', label: 'Yêu cầu của tôi' },
      { path: '/tickets', icon: 'confirmation_number', label: 'Quản lý tất cả Ticket' },
    ],
  },
  {
    label: 'GIÁM SÁT & BÁO CÁO',
    items: [
      { path: '/reports', icon: 'query_stats', label: 'Báo cáo & Thống kê SLA' },
      { path: '/network-monitor', icon: 'router', label: 'Giám sát Thiết bị mạng' },
    ],
  },
  {
    label: 'HỆ THỐNG',
    items: [
      { path: '/users', icon: 'manage_accounts', label: 'Quản lý người dùng' },
      { path: '/settings', icon: 'settings_ethernet', label: 'Cài đặt hệ thống' },
    ],
  },
]

export default function Sidebar({ mobileOpen, onClose }) {
  const location = useLocation()

  const isActive = (path) => {
    if (path === '/tickets' && location.pathname.startsWith('/tickets') && !location.pathname.startsWith('/tickets/new')) return true
    return location.pathname === path
  }

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-screen w-64 bg-[#213145] text-[#eaf1ff] z-50 flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)] transition-transform duration-300
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}
      >
        <div className="flex flex-col flex-1 overflow-y-auto">
          {/* Logo */}
          <div className="h-16 px-3 flex items-center gap-2 bg-[#213145]">
            <div className="w-8 h-8 rounded-lg bg-[#004ac6] flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-white text-[18px]">hub</span>
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-semibold text-[16px] text-[#eaf1ff] tracking-tight truncate leading-tight">NETWORK HELPDESK</span>
              <span className="font-mono text-[11px] text-[#c3c6d7] uppercase tracking-wider truncate">NOC & IT Support System</span>
            </div>
          </div>

          {/* Role selector */}
          <div className="px-3 py-2">
            <div className="bg-white/10 rounded-xl p-2 flex items-center justify-between text-[#eaf1ff]">
              <div className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-[#adc6ff]">swap_horiz</span>
                <span className="text-[11px] text-[#c3c6d7]">Vai trò demo:</span>
              </div>
              <select className="bg-transparent text-[11px] text-[#eaf1ff] focus:outline-none cursor-pointer pr-1">
                <option className="bg-[#213145] text-[#eaf1ff]">Quản trị viên (Admin)</option>
                <option className="bg-[#213145] text-[#eaf1ff]">Kỹ thuật viên (NOC Tech)</option>
                <option className="bg-[#213145] text-[#eaf1ff]">Người dùng (End User)</option>
              </select>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-1 space-y-3">
            {navSections.map((section) => (
              <div key={section.label} className="space-y-1">
                <div className="px-2 text-[11px] font-medium tracking-wider uppercase text-[#c3c6d7]">
                  {section.label}
                </div>
                {section.items.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    className={({ isActive: navActive }) => {
                      const active = navActive || isActive(item.path)
                      return `flex items-center gap-2 px-2 py-1.5 rounded-xl text-[13px] transition-all ${
                        active
                          ? 'bg-[#2563eb] text-white font-semibold'
                          : 'text-[#c3c6d7] hover:bg-white/10 hover:text-[#eaf1ff]'
                      }`
                    }}
                  >
                    <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        </div>

        {/* Logout */}
        <div className="p-2 bg-[#213145]">
          <a
            href="/accounts/logout/"
            className="flex items-center gap-2 px-2 py-1.5 rounded-xl text-[13px] text-[#c3c6d7] hover:bg-white/10 hover:text-[#eaf1ff] transition-all"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
            <span>Đăng xuất</span>
          </a>
        </div>
      </aside>
    </>
  )
}

