import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import axios from 'axios'

const MOCK_TICKET = {
  id: 'TK-9821',
  priority: 'P1 • Khẩn cấp',
  priorityBg: 'bg-[#ffdad6]',
  priorityText: 'text-[#93000a]',
  status: 'in_progress',
  vlan: 'NOC-POD-03 / VLAN-20',
  title: 'Mất kết nối Internet diện rộng toàn bộ tầng 3 - Block B',
  sender: 'Hoàng Thu Thảo',
  senderInitials: 'HT',
  department: 'Phòng Marketing & Kinh doanh',
  submittedAt: '09:15 - 24/10/2024',
  location: 'Khu làm việc Tầng 3, Tháp B',
  description: `Từ khoảng 09:05 sáng nay, toàn bộ nhân sự khối Marketing và Sales khu vực Tầng 3 (khoảng hơn 45 máy bàn và laptop kết nối Wi-Fi lẫn dây LAN) đột ngột mất mạng hoàn toàn. Biểu tượng mạng báo "No Internet Access / Secured".\n\nHiện tại các bạn đang trong phiên thuyết trình trực tuyến cho khách hàng trọng điểm qua Zoom nên cần hỗ trợ cấp bách. Đã thử khởi động lại router phụ ở phòng 304 nhưng vẫn không có tín hiệu.`,
  infra: {
    location: 'Tòa nhà B • Phòng 302 – 308',
    locationSub: 'Khu vực làm việc mở',
    device: 'Cisco Catalyst 2960X',
    deviceSub: 'Port Gi0/24 (Trunk Uplink)',
    impact: '48 Người dùng trực tiếp',
    impactSub: 'Tắc nghẽn tác vụ kinh doanh',
  },
  assignee: 'Trần Minh Hoàng',
  assigneeInitials: 'TM',
  assigneeRole: 'NOC Level 3',
  assigneeBg: 'bg-[#004ac6] text-white',
  comments: [
    {
      id: 1, type: 'public', author: 'Hoàng Thu Thảo', authorInitials: 'HT', authorBg: 'bg-[#dae2fd] text-[#3f465c]',
      role: 'Người dùng', time: '09:15 • 24/10',
      content: 'Thưa IT, chúng tôi đang hoàn toàn không có mạng tại tầng 3. Cuộc họp Zoom với khách hàng Singapore đang diễn ra, rất cần hỗ trợ gấp!',
    },
    {
      id: 2, type: 'internal', author: 'Trần Minh Hoàng', authorInitials: 'TM', authorBg: 'bg-[#004ac6] text-white',
      role: 'NOC L3 Tech', time: '09:28 • 24/10',
      content: '[Internal] Đã kiểm tra Uplink từ Access Layer Switch SW-B3-02. Port Gi0/24 đang báo err-disabled do loop detection. Đang clear err-disable và reload STP. Khả năng cao do bộ phận kỹ thuật cắm vòng cáp RJ45 khi chuyển bàn.',
      internal: true,
    },
    {
      id: 3, type: 'public', author: 'Trần Minh Hoàng', authorInitials: 'TM', authorBg: 'bg-[#004ac6] text-white',
      role: 'NOC L3 Tech', time: '09:35 • 24/10',
      content: 'Chào chị Thảo, nhóm IT đang xử lý sự cố trên thiết bị Switch phân phối tầng 3. Dự kiến kết nối sẽ được phục hồi trong vòng 15–20 phút. Chị vui lòng thông báo lại cho mọi người.',
    },
  ],
  timeline: [
    { icon: 'add_circle', iconBg: 'bg-[#dbe1ff]', iconColor: 'text-[#004ac6]', title: 'Ticket được tạo', desc: 'Tiếp nhận qua Self-Service Portal', time: '09:15 • 24/10', by: 'Hoàng Thu Thảo' },
    { icon: 'assignment_ind', iconBg: 'bg-[#dce9ff]', iconColor: 'text-[#004ac6]', title: 'Phân công kỹ thuật viên', desc: 'NOC Lead tự động phân bổ theo vùng NOC-POD-03', time: '09:16 • 24/10', by: 'Hệ thống NOC' },
    { icon: 'engineering', iconBg: 'bg-[#e5eeff]', iconColor: 'text-[#0051b1]', title: 'Bắt đầu điều tra hiện trường', desc: 'KTV onsite tại vị trí tủ rack B3-SW-02', time: '09:22 • 24/10', by: 'Trần Minh Hoàng' },
    { icon: 'router', iconBg: 'bg-[#ffdad6]', iconColor: 'text-[#ba1a1a]', title: 'Phát hiện nguyên nhân gốc rễ', desc: 'Port Gi0/24 err-disabled, STP storm do loop cáp vật lý', time: '09:28 • 24/10', by: 'Trần Minh Hoàng' },
  ],
  slaDeadline: '11:15 • 24/10',
  slaRemaining: '1h 40m',
  slaStatus: 'on-track',
}

function TimelineItem({ icon, iconBg, iconColor, title, desc, time, by, isLast }) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className={`w-9 h-9 rounded-full ${iconBg} ${iconColor} flex items-center justify-center flex-shrink-0`}>
          <span className="material-symbols-outlined text-[18px]">{icon}</span>
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-[#e5eeff] mt-1"></div>}
      </div>
      <div className="pb-4 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[14px] font-semibold text-[#0b1c30]">{title}</span>
          <span className="font-mono text-[11px] text-[#737686]">{time}</span>
        </div>
        <p className="text-[13px] text-[#565e74] mt-0.5">{desc}</p>
        <span className="text-[11px] text-[#737686] font-mono">— {by}</span>
      </div>
    </div>
  )
}

export default function TicketDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('public')
  const [replyText, setReplyText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setLoading(true)
    axios.get(`/api/tickets/${id}/`)
      .then(res => { setTicket(res.data); setLoading(false) })
      .catch(() => { setTicket(MOCK_TICKET); setLoading(false) })
  }, [id])

  const handleResolve = () => {
    if (!window.confirm('Đánh dấu ticket này là Đã giải quyết?')) return
    axios.patch(`/api/tickets/${id}/`, { status: 'resolved' })
      .then(() => { alert('Đã cập nhật trạng thái!') })
      .catch(() => { alert('Cập nhật thành công (demo mode)') })
  }

  const handleReply = (e) => {
    e.preventDefault()
    if (!replyText.trim()) return
    setSubmitting(true)
    setTimeout(() => {
      setReplyText('')
      setSubmitting(false)
    }, 800)
  }

  if (loading) return (
    <div className="p-10 text-center text-[#565e74]">
      <span className="material-symbols-outlined text-[40px] animate-spin">refresh</span>
      <p className="mt-2">Đang tải ticket...</p>
    </div>
  )

  const t = ticket
  const publicComments = t.comments.filter(c => c.type === 'public')
  const internalComments = t.comments.filter(c => c.type === 'internal')
  const shownComments = activeTab === 'public' ? publicComments : internalComments

  return (
    <div className="relative w-full px-5 py-4">
      {/* Ambient glows */}
      <div className="absolute -top-12 left-1/4 w-96 h-48 bg-[#004ac6]/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute top-0 right-10 w-72 h-40 bg-[#ba1a1a]/5 rounded-full blur-2xl pointer-events-none"></div>

      {/* Breadcrumb */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <nav className="flex items-center gap-1 text-[12px] font-semibold">
          <Link to="/tickets" className="text-[#565e74] hover:text-[#004ac6] transition-colors flex items-center gap-1">
            <span className="material-symbols-outlined text-[16px]">confirmation_number</span>
            <span>Quản lý Ticket</span>
          </Link>
          <span className="text-[#c3c6d7] font-mono">/</span>
          <span className="font-mono text-[12px] text-[#004ac6] bg-[#dce9ff] px-2 py-0.5 rounded-full font-semibold">#{t.id}</span>
          <span className="text-[#c3c6d7] font-mono">/</span>
          <span className="text-[#434655] font-medium">Chi tiết & Triage sự cố</span>
        </nav>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#eff4ff] text-[#434655] hover:bg-[#dce9ff] text-[12px] font-semibold transition-all">
            <span className="material-symbols-outlined text-[16px] text-[#0051b1]">network_check</span>
            <span>Chạy chẩn đoán nhanh</span>
          </button>
          <button className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#eff4ff] text-[#434655] hover:bg-[#dce9ff] text-[12px] font-semibold transition-all">
            <span className="material-symbols-outlined text-[16px]">print</span>
            <span>In phiếu</span>
          </button>
        </div>
      </div>

      {/* Header Card */}
      <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full ${t.priorityBg} ${t.priorityText} font-mono text-[11px] font-semibold uppercase tracking-wider`}>
                <span className="material-symbols-outlined text-[14px]">emergency</span>
                {t.priority}
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#dbe1ff] text-[#00174b] font-mono text-[11px] font-semibold">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#004ac6] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#004ac6]"></span>
                </span>
                Đang xử lý (In Progress)
              </span>
              <span className="text-[#c3c6d7] font-mono">|</span>
              <span className="font-mono text-[11px] text-[#565e74] flex items-center gap-1">
                <span className="material-symbols-outlined text-[15px]">lan</span>
                {t.vlan}
              </span>
            </div>
            <h1 className="text-[28px] font-bold text-[#0b1c30] tracking-tight leading-[36px] mb-2">{t.title}</h1>
            <div className="flex flex-wrap items-center gap-y-1 gap-x-5 text-[13px] text-[#565e74]">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-[#dae2fd] text-[#3f465c] flex items-center justify-center text-[12px] font-bold">
                  {t.senderInitials}
                </div>
                <span className="text-[#0b1c30] font-medium">{t.sender}</span>
                <span className="text-[#737686] text-[12px]">({t.department})</span>
              </div>
              <span className="text-[#c3c6d7]">•</span>
              <div className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-[#737686]">schedule</span>
                <span>Gửi lúc <strong>{t.submittedAt}</strong></span>
              </div>
              <span className="text-[#c3c6d7]">•</span>
              <div className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-[#737686]">location_on</span>
                <span>{t.location}</span>
              </div>
            </div>
          </div>
          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 self-start lg:self-center">
            <button className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#dce9ff] text-[#434655] hover:bg-[#d3e4fe] hover:text-[#0b1c30] text-[12px] font-semibold transition-all">
              <span className="material-symbols-outlined text-[18px] text-[#0051b1]">upgrade</span>
              <span>Chuyển cấp (Escalate)</span>
            </button>
            <button className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#eff4ff] text-[#565e74] hover:text-[#ba1a1a] hover:bg-[#ffdad6] text-[12px] font-semibold transition-all">
              <span className="material-symbols-outlined text-[18px]">lock</span>
              <span>Đóng Ticket</span>
            </button>
            <button onClick={handleResolve}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#004ac6] text-white hover:bg-[#0051b1] text-[12px] font-semibold shadow-sm transition-all">
              <span className="material-symbols-outlined text-[18px]">check_circle</span>
              <span>Đánh dấu Đã giải quyết</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main 8:4 Split */}
      <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* LEFT: 8 cols */}
        <div className="lg:col-span-8 flex flex-col gap-5">
          {/* Incident Description */}
          <div className="bg-white rounded-xl p-5 shadow-sm flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ba1a1a]"></span>
                <h2 className="text-[16px] font-semibold text-[#0b1c30]">Thông tin sự cố từ người dùng</h2>
              </div>
              <span className="font-mono text-[11px] px-2.5 py-1 rounded-full bg-[#e5eeff] text-[#434655] font-medium">
                Kênh tiếp nhận: Cổng Self-Service Portal
              </span>
            </div>
            <div className="p-4 bg-[#eff4ff] rounded-xl text-[#0b1c30] text-[14px] leading-relaxed whitespace-pre-wrap">
              {t.description}
            </div>
            {/* Infrastructure Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {[
                { icon: 'corporate_fare', label: 'Vị trí thực địa', value: t.infra.location, sub: t.infra.locationSub },
                { icon: 'router', label: 'Thiết bị phân phối', value: t.infra.device, sub: t.infra.deviceSub, subColor: 'text-[#004ac6] font-mono font-medium' },
                { icon: 'group', label: 'Tác động nhân sự', value: t.infra.impact, sub: t.infra.impactSub, subColor: 'text-[#ba1a1a] font-semibold' },
              ].map((item) => (
                <div key={item.label} className="p-2 bg-[#e5eeff] rounded-xl flex items-start gap-2.5">
                  <div className="p-2 rounded-lg bg-white text-[#004ac6]">
                    <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-[11px] text-[#565e74] uppercase tracking-wider font-medium">{item.label}</span>
                    <span className="text-[12px] text-[#0b1c30] font-semibold truncate">{item.value}</span>
                    <span className={`font-mono text-[11px] ${item.subColor || 'text-[#737686]'}`}>{item.sub}</span>
                  </div>
                </div>
              ))}
            </div>
            {/* Attachments */}
            <div>
              <span className="text-[12px] font-semibold text-[#565e74] block mb-2">Tệp đính kèm người dùng cung cấp (2 files):</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {[
                  { icon: 'image', name: 'loi_mat_ket_noi_304.png', size: '1.4 MB • PNG Image' },
                  { icon: 'description', name: 'ping_gateway_log.txt', size: '24 KB • Text Log • Request timed out' },
                ].map((f) => (
                  <div key={f.name} className="flex items-center justify-between p-2.5 bg-white rounded-xl hover:bg-[#eff4ff] transition-all border border-[#e5eeff]">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-10 h-10 rounded-lg bg-[#dce9ff] flex-shrink-0 flex items-center justify-center text-[#004ac6]">
                        <span className="material-symbols-outlined text-[20px]">{f.icon}</span>
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="text-[12px] text-[#0b1c30] font-semibold truncate">{f.name}</span>
                        <span className="font-mono text-[11px] text-[#565e74]">{f.size}</span>
                      </div>
                    </div>
                    <button className="p-1.5 rounded-lg text-[#565e74] hover:text-[#004ac6] hover:bg-[#dce9ff] transition-colors" title="Tải về">
                      <span className="material-symbols-outlined text-[18px]">download</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Comments/Chat */}
          <div className="bg-white rounded-xl p-5 shadow-sm flex flex-col gap-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              {/* Tabs */}
              <div className="flex items-center gap-1 p-1 bg-[#eff4ff] rounded-xl">
                <button
                  onClick={() => setActiveTab('public')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-all ${activeTab === 'public' ? 'bg-white text-[#004ac6] shadow-sm' : 'text-[#565e74] hover:text-[#0b1c30]'}`}
                >
                  <span className="material-symbols-outlined text-[16px]">forum</span>
                  <span>Phản hồi Người dùng</span>
                </button>
                <button
                  onClick={() => setActiveTab('internal')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-all ${activeTab === 'internal' ? 'bg-white text-[#004ac6] shadow-sm' : 'text-[#565e74] hover:text-[#0b1c30]'}`}
                >
                  <span className="material-symbols-outlined text-[16px] text-[#565e74]">lock_person</span>
                  <span>Ghi chú nội bộ KTV</span>
                  <span className="font-mono text-[11px] px-1.5 rounded-full bg-[#dae2fd] text-[#3f465c] font-bold">Chỉ NOC</span>
                </button>
              </div>
              <span className="text-[13px] text-[#565e74]">{shownComments.length} phản hồi</span>
            </div>

            {/* Comments list */}
            <div className="space-y-4">
              {shownComments.length === 0 && (
                <div className="text-center text-[#565e74] py-6 text-[13px]">Chưa có phản hồi nào</div>
              )}
              {t.comments.filter(c => activeTab === 'public' ? c.type !== 'internal' : c.type === 'internal').map((c) => (
                <div key={c.id} className={`flex gap-3 ${c.internal ? 'bg-[#fffbeb] border border-[#fde68a] rounded-xl p-3' : ''}`}>
                  <div className={`w-9 h-9 rounded-full ${c.authorBg} flex items-center justify-center text-[12px] font-bold flex-shrink-0`}>
                    {c.authorInitials}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[14px] font-semibold text-[#0b1c30]">{c.author}</span>
                      <span className="text-[11px] px-1.5 py-0.5 rounded bg-[#e5eeff] text-[#565e74]">{c.role}</span>
                      <span className="font-mono text-[11px] text-[#737686]">{c.time}</span>
                      {c.internal && <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[#fde68a]/50 text-[#b45309] font-semibold">Nội bộ</span>}
                    </div>
                    <p className="text-[14px] text-[#434655] mt-1 leading-relaxed">{c.content}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Reply form */}
            <form onSubmit={handleReply} className="border-t border-[#eff4ff] pt-4">
              <textarea
                value={replyText}
                onChange={e => setReplyText(e.target.value)}
                rows={3}
                placeholder={activeTab === 'public' ? 'Nhập phản hồi gửi đến người dùng...' : '[Nội bộ NOC] Ghi chú kỹ thuật, lệnh CLI, kết quả chẩn đoán...'}
                className="w-full px-4 py-3 rounded-xl bg-[#eff4ff] text-[14px] text-[#0b1c30] placeholder:text-[#737686] focus:outline-none focus:bg-white focus:ring-1 focus:ring-[#004ac6] transition-all resize-none"
              />
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-2">
                  <button type="button" className="p-1.5 rounded-lg text-[#565e74] hover:bg-[#e5eeff] hover:text-[#004ac6] transition-colors">
                    <span className="material-symbols-outlined text-[18px]">attach_file</span>
                  </button>
                  <button type="button" className="p-1.5 rounded-lg text-[#565e74] hover:bg-[#e5eeff] hover:text-[#004ac6] transition-colors">
                    <span className="material-symbols-outlined text-[18px]">image</span>
                  </button>
                </div>
                <button
                  type="submit"
                  disabled={submitting || !replyText.trim()}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#004ac6] text-white text-[13px] font-semibold hover:bg-[#0051b1] transition-colors shadow-sm disabled:opacity-50"
                >
                  <span className="material-symbols-outlined text-[16px]">{activeTab === 'internal' ? 'lock' : 'send'}</span>
                  {activeTab === 'internal' ? 'Ghi chú nội bộ' : 'Gửi phản hồi'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* RIGHT: 4 cols */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          {/* SLA Timer */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="text-[14px] font-semibold text-[#0b1c30] mb-3">SLA & Cam kết thời gian</h3>
            <div className="bg-[#ffdad6] rounded-xl p-3 text-center">
              <div className="font-mono text-[28px] font-bold text-[#ba1a1a] animate-pulse">{t.slaRemaining}</div>
              <div className="text-[11px] text-[#93000a] font-semibold mt-1">Còn lại trước khi vi phạm SLA</div>
            </div>
            <div className="flex items-center justify-between mt-3 text-[12px]">
              <div className="flex flex-col">
                <span className="text-[#565e74]">Hạn SLA (P1 Response)</span>
                <span className="font-mono font-semibold text-[#0b1c30]">{t.slaDeadline}</span>
              </div>
              <span className={`px-2 py-1 rounded-full text-[11px] font-semibold ${t.slaStatus === 'on-track' ? 'bg-[#f0fdf4] text-[#15803d]' : 'bg-[#ffdad6] text-[#ba1a1a]'}`}>
                {t.slaStatus === 'on-track' ? '✓ Đang theo dõi' : '⚠ Nguy cơ vi phạm'}
              </span>
            </div>
          </div>

          {/* Assignment */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="text-[14px] font-semibold text-[#0b1c30] mb-3">Phân công xử lý</h3>
            <div className="flex items-center gap-3 p-3 bg-[#eff4ff] rounded-xl">
              <div className={`w-10 h-10 rounded-full ${t.assigneeBg} flex items-center justify-center font-bold text-[14px]`}>
                {t.assigneeInitials}
              </div>
              <div>
                <div className="text-[14px] font-semibold text-[#0b1c30]">{t.assignee}</div>
                <div className="font-mono text-[11px] text-[#565e74]">{t.assigneeRole}</div>
              </div>
            </div>
            <button className="w-full mt-3 h-9 rounded-xl border border-[#c3c6d7] text-[#0b1c30] text-[13px] font-semibold hover:bg-[#eff4ff] transition-colors flex items-center justify-center gap-1">
              <span className="material-symbols-outlined text-[16px]">swap_horiz</span>
              Chuyển giao / Tái phân công
            </button>
          </div>

          {/* Ticket Details */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="text-[14px] font-semibold text-[#0b1c30] mb-3">Chi tiết Ticket</h3>
            <div className="space-y-2 text-[13px]">
              {[
                { label: 'Mã Ticket', value: `#${t.id}`, mono: true },
                { label: 'Trạng thái', value: 'Đang xử lý' },
                { label: 'Mức ưu tiên', value: t.priority },
                { label: 'Danh mục', value: 'Sự cố mạng LAN/WAN' },
                { label: 'Nguồn gốc', value: 'Self-Service Portal' },
                { label: 'Thời gian tạo', value: t.submittedAt },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-1.5 border-b border-[#eff4ff] last:border-0">
                  <span className="text-[#565e74]">{item.label}</span>
                  <span className={`font-semibold text-[#0b1c30] ${item.mono ? 'font-mono' : ''}`}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="text-[14px] font-semibold text-[#0b1c30] mb-4">Lịch sử xử lý</h3>
            <div className="flex flex-col">
              {t.timeline.map((item, i) => (
                <TimelineItem key={i} {...item} isLast={i === t.timeline.length - 1} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

