import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

const STATUS_STYLES = {
  open: { label: 'Mới tiếp nhận', bg: 'bg-[#eff4ff]', text: 'text-[#004ac6]', dot: 'bg-[#004ac6]' },
  in_progress: { label: 'Đang xử lý', bg: 'bg-[#dce9ff]', text: 'text-[#004ac6]', dot: 'bg-[#004ac6]', pulse: true },
  resolved: { label: 'Đã giải quyết', bg: 'bg-[#f0fdf4]', text: 'text-[#15803d]', dot: 'bg-[#22c55e]' },
  closed: { label: 'Đã đóng', bg: 'bg-[#f1f5f9]', text: 'text-[#475569]', dot: 'bg-[#64748b]' },
}

const PRIORITY_STYLES = {
  p1: { label: 'P1 Khẩn cấp', bg: 'bg-[#ffdad6]', text: 'text-[#ba1a1a]', icon: 'emergency' },
  p2: { label: 'P2 Cao', bg: 'bg-[#dae2fd]', text: 'text-[#3f465c]', icon: 'arrow_upward' },
  p3: { label: 'P3 Vừa', bg: 'bg-[#dce9ff]', text: 'text-[#0b1c30]', icon: 'drag_handle' },
  p4: { label: 'P4 Thấp', bg: 'bg-[#eff4ff]', text: 'text-[#565e74]', icon: 'arrow_downward' },
}

const CATEGORY_ICONS = {
  internet: { icon: 'router', color: 'text-[#ba1a1a]', label: 'Mất mạng' },
  wifi: { icon: 'wifi', color: 'text-[#004ac6]', label: 'Lỗi Wi-Fi' },
  server: { icon: 'dns', color: 'text-[#ba1a1a]', label: 'Máy chủ' },
  switch: { icon: 'hub', color: 'text-[#565e74]', label: 'Switch/Router' },
  vpn: { icon: 'vpn_lock', color: 'text-[#0051b1]', label: 'VPN / FW' },
  peripheral: { icon: 'print', color: 'text-[#565e74]', label: 'Thiết bị ngoại vi' },
}

// Mock ticket data
const MOCK_TICKETS = [
  {
    id: 'TK-8901', sender: 'Võ Hoàng Yến', department: 'Phòng Kế toán', ip: '192.168.10.45',
    title: 'Mất kết nối mạng toàn bộ tầng 3 khối Tài chính',
    desc: 'Switch Cisco Catalyst 2960 tầng 3 mất nguồn, đèn Port báo cam...',
    category: 'internet', time: '10:42 SA', date: 'Hôm nay',
    priority: 'p1', assignee: 'Trần Minh Hoàng', assigneeInitials: 'TM', assigneeBg: 'bg-[#004ac6] text-white',
    status: 'in_progress', critical: true,
  },
  {
    id: 'TK-8900', sender: 'Phạm Quốc Bảo', department: 'Ban Giám Đốc', ip: 'VPN Client',
    title: 'Không thể xác thực VPN FortiClient từ ngoài mạng văn phòng',
    desc: 'Báo lỗi TLS handshake timeout, nhân sự WFH không truy cập được ERP nội bộ...',
    category: 'vpn', time: '10:15 SA', date: 'Hôm nay',
    priority: 'p2', assignee: 'Lê Văn An', assigneeInitials: 'LV', assigneeBg: 'bg-[#0051b1] text-white',
    status: 'in_progress',
  },
  {
    id: 'TK-8898', sender: 'Đặng Thùy Trang', department: 'Hành chính', ip: 'Phòng Họp VIP 1',
    title: 'Sóng Wi-Fi chập chờn, rớt mạng liên tục tại phòng họp VIP',
    desc: 'Access Point AP-VIP-01 báo đèn đỏ ngắt quãng, khách đối tác không bắt được sóng...',
    category: 'wifi', time: '09:48 SA', date: 'Hôm nay',
    priority: 'p3', assignee: 'Nguyễn Hải Đăng', assigneeInitials: 'NH', assigneeBg: 'bg-[#565e74] text-white',
    status: 'open',
  },
  {
    id: 'TK-8895', sender: 'Trịnh Đình Quang', department: 'Kỹ thuật Hệ thống', ip: 'DC-01',
    title: 'Máy chủ Database MSSQL quá tải kết nối I/O 99%',
    desc: 'Hệ thống thanh toán API trễ > 8000ms, nghi ngờ nghẽn card mạng NIC-Bonding...',
    category: 'server', time: '09:12 SA', date: 'Hôm nay',
    priority: 'p1', assignee: 'Trần Minh Hoàng', assigneeInitials: 'TM', assigneeBg: 'bg-[#004ac6] text-white',
    status: 'in_progress', critical: true,
  },
  {
    id: 'TK-8891', sender: 'Lương Bích Hữu', department: 'Marketing', ip: 'Máy in màu P6',
    title: 'Trùng địa chỉ IP máy in mạng Canon LBP Tầng 2',
    desc: 'Yêu cầu cấu hình đặt IP Tĩnh (Static IP) và gắn DHCP Reservation...',
    category: 'peripheral', time: '08:30 SA', date: 'Hôm nay',
    priority: 'p4', assignee: null, assigneeInitials: null,
    status: 'open',
  },
  {
    id: 'TK-8884', sender: 'NOC Bot Auto-Alert', department: 'Hệ thống Giám sát', ip: 'Gateway VNPT',
    title: 'Đứt cáp quang tuyến Leased Line Viettel 1Gbps sang VNPT Backup',
    desc: 'BGP tự động chuyển mạch sang tuyến dự phòng trong 4.2 giây, đã nối lại cáp quang...',
    category: 'internet', time: '11/10', date: 'Hôm qua',
    priority: 'p1', assignee: 'Lê Hồng Phong', assigneeInitials: 'LH', assigneeBg: 'bg-[#565e74] text-white',
    status: 'resolved',
  },
]

function StatusBadge({ status }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.open
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${s.bg} ${s.text} text-[11px] font-semibold`}>
      <span className={`w-2 h-2 rounded-full ${s.dot} ${s.pulse ? 'animate-pulse' : ''}`}></span>
      {s.label}
    </span>
  )
}

function PriorityBadge({ priority }) {
  const p = PRIORITY_STYLES[priority] || PRIORITY_STYLES.p3
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${p.bg} ${p.text} text-[11px] font-semibold`}>
      <span className="material-symbols-outlined text-[14px]">{p.icon}</span>
      {p.label}
    </span>
  )
}

export default function TicketList() {
  const [tickets, setTickets] = useState(MOCK_TICKETS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [selected, setSelected] = useState([])

  const kpis = [
    { label: 'Tổng Ticket Đang Mở', value: '142', sub: '+8 hôm nay', subColor: 'text-[#004ac6]', icon: 'confirmation_number', iconBg: 'bg-[#eff4ff]', iconColor: 'text-[#004ac6]' },
    { label: 'Khẩn cấp (P1 Critical)', value: '04', sub: 'SLA < 30 phút', subColor: 'text-[#434655]', icon: 'warning', iconBg: 'bg-[#ffdad6]/40', iconColor: 'text-[#ba1a1a]', urgent: true },
    { label: 'Đang Xử Lý (In Progress)', value: '39', sub: '9 Kỹ thuật viên', subColor: 'text-[#0051b1]', icon: 'pending_actions', iconBg: 'bg-[#dce9ff]/60', iconColor: 'text-[#0051b1]' },
    { label: 'Tỷ Lệ Đạt Cam Kết SLA', value: '98.4%', sub: 'MTTR: 24m', subColor: 'text-[#565e74]', icon: 'verified', iconBg: 'bg-[#eff4ff]', iconColor: 'text-[#004ac6]' },
  ]

  useEffect(() => {
    setLoading(true)
    axios.get('/api/tickets/')
      .then(res => {
        if (res.data && res.data.length > 0) setTickets(res.data)
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
        setError('Hiển thị dữ liệu mẫu — API /api/tickets/ chưa sẵn sàng')
      })
  }, [])

  const filtered = tickets.filter(t => {
    const matchSearch = !search || t.title.toLowerCase().includes(search.toLowerCase()) || t.id.toLowerCase().includes(search.toLowerCase()) || t.sender.toLowerCase().includes(search.toLowerCase())
    const matchStatus = statusFilter === 'all' || t.status === statusFilter
    const matchPriority = priorityFilter === 'all' || t.priority === priorityFilter
    const matchCategory = categoryFilter === 'all' || t.category === categoryFilter
    return matchSearch && matchStatus && matchPriority && matchCategory
  })

  const toggleSelect = (id) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const toggleAll = (checked) => {
    setSelected(checked ? filtered.map(t => t.id) : [])
  }

  return (
    <div className="px-5 py-5 flex flex-col gap-5 max-w-[1600px] w-full mx-auto">
      {/* KPI bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {kpis.map((k) => (
          <div key={k.label} className="bg-white p-3 rounded-xl shadow-sm flex items-center justify-between">
            <div className="flex flex-col min-w-0">
              <span className={`text-[11px] font-medium uppercase tracking-wider ${k.urgent ? 'text-[#ba1a1a] flex items-center gap-1' : 'text-[#434655]'}`}>
                {k.urgent && <span className="w-2 h-2 rounded-full bg-[#ba1a1a] animate-ping"></span>}
                {k.label}
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className={`text-[28px] font-bold leading-[36px] ${k.urgent ? 'text-[#ba1a1a]' : 'text-[#0b1c30]'}`}>{k.value}</span>
                <span className={`text-[11px] font-medium ${k.subColor}`}>{k.sub}</span>
              </div>
            </div>
            <div className={`w-10 h-10 rounded-xl ${k.iconBg} flex items-center justify-center ${k.iconColor}`}>
              <span className="material-symbols-outlined text-[22px]">{k.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main table card */}
      <div className="bg-white rounded-xl shadow-sm flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-3 bg-white">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <h2 className="text-[20px] font-semibold text-[#0b1c30]">Quản lý Tất cả Ticket</h2>
              <span className="px-2 py-0.5 rounded-full bg-[#004ac6]/10 text-[#004ac6] font-mono text-[11px] font-semibold">{filtered.length} tổng</span>
            </div>
            <p className="text-[13px] text-[#434655] mt-0.5">Giám sát, phân luồng sự cố mạng LAN/WAN, máy chủ và hỗ trợ kỹ thuật người dùng toàn doanh nghiệp.</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button className="h-9 px-3 rounded-xl bg-[#eff4ff] hover:bg-[#e5eeff] text-[#0b1c30] text-[14px] font-medium flex items-center gap-1 transition-colors shadow-sm">
              <span className="material-symbols-outlined text-[18px] text-[#565e74]">file_download</span>
              <span>Xuất Excel / Báo cáo</span>
            </button>
            <Link to="/tickets/new">
              <button className="h-9 px-3 rounded-xl bg-[#004ac6] hover:bg-[#0051b1] text-white text-[14px] font-semibold flex items-center gap-1 transition-colors shadow-sm">
                <span className="material-symbols-outlined text-[18px]">add</span>
                <span>Tạo Ticket hỗ trợ mới</span>
              </button>
            </Link>
          </div>
        </div>

        {/* Error notice */}
        {error && (
          <div className="mx-4 mb-2 bg-[#fffbeb] border border-[#fde68a] text-[#b45309] rounded-xl px-4 py-2 text-[13px]">
            ⚠️ {error}
          </div>
        )}

        {/* Filters */}
        <div className="px-4 pb-4 sm:px-5 flex flex-col gap-2 bg-white">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
            {/* Search */}
            <div className="lg:col-span-2 relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-[#737686]">search</span>
              <input
                type="text" value={search} onChange={e => setSearch(e.target.value)}
                className="w-full h-10 pl-9 pr-8 rounded-xl bg-[#eff4ff] text-[14px] text-[#0b1c30] placeholder:text-[#737686] focus:outline-none focus:bg-white shadow-sm transition-all"
                placeholder="Tìm theo Mã Ticket, Tiêu đề, Người gửi, IP thiết bị..."
              />
            </div>
            {/* Status */}
            <div className="relative">
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
                className="w-full h-10 px-3 pr-8 rounded-xl bg-[#eff4ff] text-[14px] text-[#0b1c30] appearance-none focus:outline-none shadow-sm cursor-pointer">
                <option value="all">Trạng thái: Tất cả</option>
                <option value="open">Mới tiếp nhận (Open)</option>
                <option value="in_progress">Đang xử lý (In Progress)</option>
                <option value="resolved">Đã giải quyết (Resolved)</option>
                <option value="closed">Đã đóng (Closed)</option>
              </select>
              <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-[18px] text-[#737686] pointer-events-none">expand_more</span>
            </div>
            {/* Priority */}
            <div className="relative">
              <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)}
                className="w-full h-10 px-3 pr-8 rounded-xl bg-[#eff4ff] text-[14px] text-[#0b1c30] appearance-none focus:outline-none shadow-sm cursor-pointer">
                <option value="all">Ưu tiên: Tất cả</option>
                <option value="p1">P1 - Khẩn cấp (Critical)</option>
                <option value="p2">P2 - Cao (High)</option>
                <option value="p3">P3 - Trung bình (Medium)</option>
                <option value="p4">P4 - Thấp (Low)</option>
              </select>
              <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-[18px] text-[#737686] pointer-events-none">expand_more</span>
            </div>
            {/* Category */}
            <div className="relative">
              <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}
                className="w-full h-10 px-3 pr-8 rounded-xl bg-[#eff4ff] text-[14px] text-[#0b1c30] appearance-none focus:outline-none shadow-sm cursor-pointer">
                <option value="all">Loại sự cố: Tất cả</option>
                <option value="internet">Mất mạng Internet</option>
                <option value="wifi">Lỗi Wi-Fi Access Point</option>
                <option value="server">Lỗi Máy chủ / Server</option>
                <option value="switch">Thiết bị Switch / Router</option>
                <option value="vpn">Kết nối VPN / Firewall</option>
              </select>
              <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-[18px] text-[#737686] pointer-events-none">expand_more</span>
            </div>
            {/* Assignee */}
            <div className="relative">
              <select className="w-full h-10 px-3 pr-8 rounded-xl bg-[#eff4ff] text-[14px] text-[#0b1c30] appearance-none focus:outline-none shadow-sm cursor-pointer">
                <option value="all">Kỹ thuật viên: Tất cả</option>
                <option>Trần Minh Hoàng</option>
                <option>Lê Văn An</option>
                <option>Nguyễn Hải Đăng</option>
                <option>Chưa gán kỹ thuật</option>
              </select>
              <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-[18px] text-[#737686] pointer-events-none">expand_more</span>
            </div>
          </div>

          {/* Quick filters */}
          <div className="flex items-center justify-between flex-wrap gap-1 pt-1">
            <div className="flex items-center gap-1 flex-wrap">
              <span className="text-[11px] text-[#737686]">Lọc nhanh:</span>
              <button className="px-2.5 py-1 rounded-full bg-[#ffdad6]/50 text-[#93000a] text-[11px] font-semibold hover:bg-[#ffdad6] transition-colors flex items-center gap-1"
                onClick={() => { setPriorityFilter('p1'); setStatusFilter('open') }}>
                <span className="w-1.5 h-1.5 rounded-full bg-[#ba1a1a]"></span> Sự cố P1 chưa xử lý (3)
              </button>
              <button className="px-2.5 py-1 rounded-full bg-[#eff4ff] text-[#434655] text-[11px] hover:bg-[#e5eeff] hover:text-[#0b1c30] transition-colors">
                Chưa gán kỹ thuật viên (14)
              </button>
              <button className="px-2.5 py-1 rounded-full bg-[#eff4ff] text-[#434655] text-[11px] hover:bg-[#e5eeff] hover:text-[#0b1c30] transition-colors">
                Gần quá hạn SLA (&lt;15m) (2)
              </button>
            </div>
            <button className="text-[14px] text-[#004ac6] hover:underline flex items-center gap-1"
              onClick={() => { setSearch(''); setStatusFilter('all'); setPriorityFilter('all'); setCategoryFilter('all') }}>
              <span className="material-symbols-outlined text-[16px]">restart_alt</span> Đặt lại bộ lọc
            </button>
          </div>
        </div>

        {/* Batch action bar */}
        {selected.length > 0 && (
          <div className="px-4 py-2 bg-[#213145] text-[#eaf1ff] flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <span className="w-5 h-5 rounded-full bg-[#004ac6] flex items-center justify-center font-mono text-[11px] text-white font-bold">{selected.length}</span>
                <span className="text-[14px]">ticket đã được chọn</span>
              </div>
              <div className="hidden sm:flex items-center gap-1">
                <button className="h-8 px-2 rounded-xl bg-white/20 hover:bg-white/30 text-[#eaf1ff] text-[11px] font-semibold flex items-center gap-1 transition-colors">
                  <span className="material-symbols-outlined text-[16px]">person_add</span> Gán Kỹ thuật viên
                </button>
                <button className="h-8 px-2 rounded-xl bg-white/20 hover:bg-white/30 text-[#eaf1ff] text-[11px] font-semibold flex items-center gap-1 transition-colors">
                  <span className="material-symbols-outlined text-[16px]">change_circle</span> Chuyển trạng thái
                </button>
              </div>
            </div>
            <button className="text-[11px] text-[#c3c6d7] hover:text-[#eaf1ff] flex items-center gap-1" onClick={() => setSelected([])}>
              <span className="material-symbols-outlined text-[16px]">close</span> Bỏ chọn
            </button>
          </div>
        )}

        {/* Table */}
        <div className="w-full overflow-x-auto">
          {loading ? (
            <div className="p-10 text-center text-[#565e74]">
              <span className="material-symbols-outlined text-[40px] animate-spin">refresh</span>
              <p className="mt-2">Đang tải dữ liệu...</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#eff4ff] text-[#434655] text-[11px] font-medium uppercase tracking-wider select-none">
                  <th className="py-3 px-4 w-12 text-center">
                    <input type="checkbox" className="w-4 h-4 rounded cursor-pointer accent-[#004ac6]"
                      checked={selected.length === filtered.length && filtered.length > 0}
                      onChange={e => toggleAll(e.target.checked)}
                    />
                  </th>
                  <th className="py-3 px-3 w-28">Mã Ticket</th>
                  <th className="py-3 px-3 w-56">Người gửi / Phòng ban</th>
                  <th className="py-3 px-3 min-w-[280px]">Tiêu đề sự cố</th>
                  <th className="py-3 px-3 w-36">Loại sự cố</th>
                  <th className="py-3 px-3 w-36">Thời gian gửi</th>
                  <th className="py-3 px-3 w-32">Mức ưu tiên</th>
                  <th className="py-3 px-3 w-44">Kỹ thuật viên</th>
                  <th className="py-3 px-3 w-36">Trạng thái</th>
                  <th className="py-3 px-4 w-28 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eff4ff]">
                {filtered.map((t) => {
                  const cat = CATEGORY_ICONS[t.category] || { icon: 'help', color: 'text-[#565e74]', label: t.category }
                  const isSelected = selected.includes(t.id)
                  return (
                    <tr
                      key={t.id}
                      className={`hover:bg-[#eff4ff]/60 transition-colors group cursor-pointer ${isSelected ? 'bg-[#eff4ff]' : ''}`}
                      onClick={() => window.location.href = `/tickets/${t.id}`}
                    >
                      <td className="py-3.5 px-4 text-center" onClick={e => { e.stopPropagation(); toggleSelect(t.id) }}>
                        <input type="checkbox" className="w-4 h-4 rounded cursor-pointer accent-[#004ac6]"
                          checked={isSelected} onChange={() => {}} />
                      </td>
                      <td className="py-3.5 px-3">
                        <span className="font-mono text-[12px] font-semibold text-[#004ac6] px-2 py-0.5 bg-[#004ac6]/10 rounded-lg">#{t.id}</span>
                      </td>
                      <td className="py-3.5 px-3">
                        <div className="flex flex-col min-w-0">
                          <span className="text-[13px] font-semibold text-[#0b1c30] truncate">{t.sender}</span>
                          <span className="font-mono text-[11px] text-[#434655] truncate">{t.department} • IP: {t.ip}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3">
                        <div className="flex flex-col min-w-0 pr-2">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[14px] font-semibold text-[#0b1c30] truncate">{t.title}</span>
                            {t.critical && <span className="w-1.5 h-1.5 rounded-full bg-[#ba1a1a] shrink-0"></span>}
                          </div>
                          <span className="text-[13px] text-[#434655] truncate">{t.desc}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3">
                        <div className={`flex items-center gap-1.5 text-[#0b1c30] text-[13px]`}>
                          <span className={`material-symbols-outlined text-[18px] ${cat.color}`}>{cat.icon}</span>
                          <span>{cat.label}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3">
                        <div className="flex flex-col">
                          <span className="font-mono text-[11px] text-[#0b1c30] font-medium">{t.time}</span>
                          <span className="font-mono text-[11px] text-[#434655]">{t.date}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3">
                        <PriorityBadge priority={t.priority} />
                      </td>
                      <td className="py-3.5 px-3">
                        {t.assignee ? (
                          <div className="flex items-center gap-2">
                            <div className={`w-6 h-6 rounded-full ${t.assigneeBg || 'bg-[#565e74] text-white'} flex items-center justify-center font-mono text-[10px] font-bold`}>
                              {t.assigneeInitials}
                            </div>
                            <span className="text-[13px] text-[#0b1c30] truncate">{t.assignee}</span>
                          </div>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-[#e5eeff] text-[#434655] font-mono text-[11px]">Chưa gán</span>
                        )}
                      </td>
                      <td className="py-3.5 px-3">
                        <StatusBadge status={t.status} />
                      </td>
                      <td className="py-3.5 px-4 text-right" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1">
                          <Link to={`/tickets/${t.id}`}>
                            <button className="p-1 rounded-lg text-[#434655] hover:text-[#004ac6] hover:bg-[#e5eeff] transition-colors" title="Xem chi tiết">
                              <span className="material-symbols-outlined text-[18px]">visibility</span>
                            </button>
                          </Link>
                          <button className="p-1 rounded-lg text-[#434655] hover:text-[#004ac6] hover:bg-[#e5eeff] transition-colors" title="Giao việc nhanh">
                            <span className="material-symbols-outlined text-[18px]">assignment_ind</span>
                          </button>
                          <button className="p-1 rounded-lg text-[#434655] hover:text-[#004ac6] hover:bg-[#e5eeen] transition-colors" title="Tùy chọn khác">
                            <span className="material-symbols-outlined text-[18px]">more_vert</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}

          {!loading && filtered.length === 0 && (
            <div className="p-10 text-center text-[#565e74]">
              <span className="material-symbols-outlined text-[48px]">search_off</span>
              <p className="mt-2 text-[15px]">Không tìm thấy ticket nào phù hợp</p>
              <p className="text-[13px] mt-1">Thử thay đổi bộ lọc hoặc từ khoá tìm kiếm</p>
            </div>
          )}
        </div>

        {/* Pagination */}
        <div className="p-4 flex items-center justify-between border-t border-[#eff4ff]">
          <span className="text-[13px] text-[#565e74]">Hiển thị {filtered.length} trong tổng số 1,284 ticket</span>
          <div className="flex items-center gap-1">
            <button className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-[#eff4ff] text-[#565e74] transition-colors">
              <span className="material-symbols-outlined text-[18px]">chevron_left</span>
            </button>
            {[1, 2, 3, '...', 128].map((p, i) => (
              <button key={i} className={`h-8 min-w-[32px] px-2 flex items-center justify-center rounded-lg text-[13px] transition-colors ${p === 1 ? 'bg-[#004ac6] text-white' : 'hover:bg-[#eff4ff] text-[#565e74]'}`}>
                {p}
              </button>
            ))}
            <button className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-[#eff4ff] text-[#565e74] transition-colors">
              <span className="material-symbols-outlined text-[18px]">chevron_right</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

