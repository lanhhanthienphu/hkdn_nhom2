import { useState } from 'react'

export default function Header({ onMenuToggle }) {
  const [searchVal, setSearchVal] = useState('')

  return (
    <header className="fixed top-0 left-0 md:left-64 right-0 h-16 bg-white/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 flex items-center justify-between px-5">
      {/* Mobile menu button */}
      <button
        className="md:hidden p-2 rounded-xl text-[#434655] hover:bg-[#eff4ff] mr-2 transition-colors"
        onClick={onMenuToggle}
      >
        <span className="material-symbols-outlined text-[22px]">menu</span>
      </button>

      {/* Search */}
      <div className="flex items-center gap-3 flex-1 max-w-xl">
        <div className="relative w-full">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-[#737686]">search</span>
          <input
            type="text"
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="w-full h-10 pl-9 pr-3 rounded-xl bg-[#eff4ff] text-[14px] text-[#0b1c30] placeholder:text-[#737686] focus:outline-none focus:bg-white focus:ring-1 focus:ring-[#004ac6] transition-all"
            placeholder="Tìm kiếm Ticket, mã IP, máy trạm, switch, tên nhân sự... (Ctrl+K)"
          />
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3">
        {/* Network status */}
        <div className="hidden xl:flex items-center gap-1 px-2 py-1 rounded-full bg-[#eff4ff] text-[#0b1c30]">
          <span className="w-2 h-2 rounded-full bg-[#004ac6] animate-pulse"></span>
          <span className="text-[11px] text-[#434655]">Hạ tầng mạng:</span>
          <span className="font-mono text-[11px] text-[#004ac6] font-semibold">99.98% Uptime</span>
        </div>

        {/* Notifications */}
        <button className="relative p-1.5 rounded-xl text-[#434655] hover:bg-[#eff4ff] hover:text-[#0b1c30] transition-all">
          <span className="material-symbols-outlined text-[22px]">notifications</span>
          <span className="absolute top-1.5 right-1.5 flex h-4 min-w-[16px] px-1 items-center justify-center rounded-full bg-[#ba1a1a] text-white font-mono text-[10px] font-bold leading-none">4</span>
        </button>

        {/* User profile */}
        <div className="flex items-center gap-2 pl-2">
          <div className="flex flex-col text-right hidden sm:flex">
            <span className="text-[12px] font-semibold text-[#0b1c30] truncate">Nguyễn Văn Tuấn</span>
            <span className="font-mono text-[11px] text-[#434655] truncate">Quản trị viên / NOC Lead</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-[#004ac6] flex items-center justify-center">
            <span className="material-symbols-outlined text-white text-[18px]">person</span>
          </div>
          <span className="material-symbols-outlined text-[#737686] text-[18px] cursor-pointer hover:text-[#0b1c30]">expand_more</span>
        </div>
      </div>
    </header>
  )
}

