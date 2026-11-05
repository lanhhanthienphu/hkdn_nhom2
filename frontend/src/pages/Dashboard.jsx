import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

// KPI Stats Card
function StatCard({ label, value, sub, subColor, icon, iconBg, iconColor, animate }) {
  return (
    <div className="bg-white p-3 rounded-xl shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <span className={`text-[13px] ${subColor || 'text-[#565e74]'} font-medium`}>{label}</span>
        <div className={`w-8 h-8 rounded-lg ${iconBg} ${iconColor} flex items-center justify-center ${animate ? 'animate-pulse' : ''}`}>
          <span className="material-symbols-outlined text-[18px]">{icon}</span>
        </div>
      </div>
      <div className="mt-2">
        <div className={`text-[28px] font-bold leading-[36px] ${subColor || 'text-[#0b1c30]'}`}>{value}</div>
        {sub && <div className="mt-1 text-[11px] font-mono">{sub}</div>}
      </div>
    </div>
  )
}

// Network Device Card
function NetworkCard({ icon, label, name, status, statusColor, detail }) {
  return (
    <div className="bg-[#eff4ff] p-3 rounded-xl flex items-center gap-3">
      <div className="w-12 h-12 rounded-xl bg-[#d3e4fe] text-[#004ac6] flex items-center justify-center flex-shrink-0">
        <span className="material-symbols-outlined text-[24px]">{icon}</span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between">
          <span className="text-[12px] font-semibold text-[#565e74]">{label}</span>
          <span className={`text-[11px] font-mono font-semibold ${statusColor || 'text-[#004ac6]'}`}>{status}</span>
        </div>
        <div className="text-[16px] font-semibold text-[#0b1c30] truncate">{name}</div>
        {detail}
      </div>
    </div>
  )
}

// Priority Bar
function PriorityBar({ icon, label, labelColor, count, pct, barColor }) {
  return (
    <div>
      <div className="flex items-center justify-between text-[12px] font-semibold mb-1">
        <span className={`flex items-center gap-1.5 ${labelColor}`}>
          <span className="material-symbols-outlined text-[16px]">{icon}</span> {label}
        </span>
        <span className={`font-mono text-[11px] font-bold ${labelColor}`}>{count}</span>
      </div>
      <div className="w-full bg-[#dce9ff] h-2 rounded-full overflow-hidden">
        <div className={`${barColor} h-full rounded-full`} style={{ width: pct }}></div>
      </div>
    </div>
  )
}

// Emergency Ticket Row
function EmergencyRow({ id, priority, priorityColor, title, desc, location, locationSub, reporter, reporterSub, assignee, assigneeInitials, slaText, slaColor, slaBg, action, actionStyle }) {
  return (
    <tr className="hover:bg-[#eff4ff]/70 transition-colors">
      <td className="py-3 px-3">
        <span className="font-mono text-[12px] font-bold text-[#004ac6]">{id}</span>
        <span className={`block font-mono text-[11px] font-semibold ${priorityColor}`}>{priority}</span>
      </td>
      <td className="py-3 px-3">
        <div className="text-[14px] font-semibold text-[#0b1c30]">{title}</div>
        <div className="text-[13px] text-[#565e74] truncate max-w-sm">{desc}</div>
      </td>
      <td className="py-3 px-3 text-[#0b1c30] text-[13px]">
        <div className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[16px] text-[#565e74]">apartment</span>
          <span>{location}</span>
        </div>
        <div className="text-[#565e74] font-mono text-[11px]">{locationSub}</div>
      </td>
      <td className="py-3 px-3">
        <div className="font-medium text-[#0b1c30] text-[13px]">{reporter}</div>
        <div className="text-[#565e74] font-mono text-[11px]">{reporterSub}</div>
      </td>
      <td className="py-3 px-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-[#004ac6] text-white flex items-center justify-center font-mono text-[11px] font-bold">
            {assigneeInitials}
          </div>
          <div>
            <span className="font-medium text-[#0b1c30] text-[13px]">{assignee}</span>
          </div>
        </div>
      </td>
      <td className="py-3 px-3">
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md ${slaBg} ${slaColor} font-mono text-[11px] font-bold ${slaText.includes('18') || slaText.includes('32') ? 'animate-pulse' : ''}`}>
          <span className="material-symbols-outlined text-[14px]">alarm</span>
          {slaText}
        </span>
      </td>
      <td className="py-3 px-3 text-right">
        <div className="inline-flex items-center gap-1.5">
          <Link to={`/tickets/1`}>
            <button className={`px-2 py-1.5 rounded-lg ${actionStyle} text-[11px] font-semibold hover:opacity-90 transition-colors shadow-sm`}>
              {action}
            </button>
          </Link>
          <button className="p-1.5 rounded-lg hover:bg-[#dce9ff] text-[#565e74] hover:text-[#0b1c30] transition-colors">
            <span className="material-symbols-outlined text-[18px]">more_vert</span>
          </button>
        </div>
      </td>
    </tr>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [period, setPeriod] = useState('today')

  useEffect(() => {
    // Try to fetch real stats, fallback to mock data
    axios.get('/api/tickets/stats/')
      .then(res => {
        setStats(res.data)
        setLoading(false)
      })
      .catch(() => {
        // Use mock data if API not available
        setStats({
          total: 1284, new: 28, inProgress: 45, urgent: 6, resolved: 1180, slaRate: '98.4%'
        })
        setLoading(false)
        setError('API chưa sẵn sàng — đang hiển thị dữ liệu mẫu')
      })
  }, [])

  const emergencyTickets = [
    {
      id: '#TK-8942', priority: 'P1 • Critical', priorityColor: 'text-[#ba1a1a]',
      title: 'Sập Switch Tầng 4 Tòa Nhà FPT',
      desc: 'Mất tín hiệu kết nối toàn bộ VLAN 20 & 30, đèn cổng quang tắt ngấm.',
      location: 'Tòa FPT - Tầng 4', locationSub: 'Rack Cabinet B4-02',
      reporter: 'Trần Minh Hoàng', reporterSub: 'Khối Phát triển PM',
      assignee: 'Nguyễn Văn Tuấn', assigneeInitials: 'NV',
      slaText: 'Còn 18 phút', slaColor: 'text-[#ba1a1a]', slaBg: 'bg-[#ffdad6]',
      action: 'Xử Lý Ngay', actionStyle: 'bg-[#004ac6] text-white',
    },
    {
      id: '#TK-8939', priority: 'P1 • Critical', priorityColor: 'text-[#ba1a1a]',
      title: 'Mất Kết Nối Gateway Core Router',
      desc: 'Mất routing BGP peering với nhà mạng Viettel, rớt tuyến dự phòng.',
      location: 'Data Center DC-01', locationSub: 'Core Rack DC-C1',
      reporter: 'Hệ thống Zabbix Bot', reporterSub: 'Auto Alarm Incident',
      assignee: 'Lê Hồng Phong', assigneeInitials: 'LH',
      slaText: 'Còn 32 phút', slaColor: 'text-[#ba1a1a]', slaBg: 'bg-[#ffdad6]',
      action: 'Xử Lý Ngay', actionStyle: 'bg-[#004ac6] text-white',
    },
    {
      id: '#TK-8935', priority: 'P2 • High', priorityColor: 'text-[#0051b1]',
      title: 'Lỗi DHCP Server Phòng Server 02',
      desc: 'Pool cấp phát IP 192.168.10.0/24 đầy 100%, máy trạm mới không nhận mạng.',
      location: 'Phòng Server 02', locationSub: 'DHCP-SRV-WIN02',
      reporter: 'Đỗ Thùy Trang', reporterSub: 'Phòng Kế Toán',
      assignee: 'Đoàn Đức Huy', assigneeInitials: 'ĐD',
      slaText: 'Còn 45 phút', slaColor: 'text-[#0051b1]', slaBg: 'bg-[#e5eeff]',
      action: 'Điều Phối', actionStyle: 'bg-[#e5eeff] text-[#0051b1]',
    },
  ]

  return (
    <div className="px-5 py-5 space-y-5 max-w-[1680px] mx-auto w-full">
      {/* Header banner */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 bg-white p-5 rounded-xl shadow-sm">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#dce9ff] text-[#004ac6] font-mono text-[11px] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-[#004ac6] animate-ping"></span>
              NOC COMMAND CENTER • LIVE MONITORING
            </span>
            <span className="text-[#565e74] font-mono text-[11px]">
              Cập nhật: {new Date().toLocaleTimeString('vi-VN')} GMT+7
            </span>
          </div>
          <h1 className="text-[28px] font-bold text-[#0b1c30] tracking-tight leading-[36px]">
            Bảng Điều Khiển NOC & Giám Sát Kỹ Thuật
          </h1>
          <p className="text-[14px] text-[#565e74]">
            Trung tâm điều phối vận hành sự cố hạ tầng mạng, chất lượng dịch vụ SLA và hàng đợi xử lý kỹ thuật viên.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex p-1 rounded-xl bg-[#eff4ff]">
            {['Hôm nay', '7 ngày', '30 ngày'].map((p, i) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-colors ${period === p ? 'bg-white text-[#004ac6] shadow-sm' : 'text-[#565e74] hover:text-[#0b1c30]'}`}
              >
                {p}
              </button>
            ))}
          </div>
          <button className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-[#eff4ff] text-[#0b1c30] hover:bg-[#dce9ff] transition-colors text-[12px] font-semibold">
            <span className="material-symbols-outlined text-[18px]">download</span>
            <span>Xuất Báo Cáo</span>
          </button>
          <button className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-[#004ac6] text-white hover:bg-[#0051b1] transition-colors shadow-sm text-[12px] font-semibold">
            <span className="material-symbols-outlined text-[18px]">refresh</span>
            <span>Làm Mới Trực Tiếp</span>
          </button>
        </div>
      </div>

      {/* API Error notice */}
      {error && (
        <div className="bg-[#fffbeb] border border-[#fde68a] text-[#b45309] rounded-xl px-4 py-2 text-[13px]">
          ⚠️ {error}
        </div>
      )}

      {/* KPI Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <StatCard
          label="Tổng số Ticket" value={loading ? '...' : (stats?.total || 1284)}
          sub={<span className="text-[#004ac6] font-semibold flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">trending_up</span>+12% tuần này</span>}
          icon="receipt_long" iconBg="bg-[#eff4ff]" iconColor="text-[#004ac6]"
        />
        <StatCard
          label="Tiếp nhận mới" value={loading ? '...' : (stats?.new || 28)}
          sub={<span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#dce9ff] text-[#004ac6] font-semibold">Cần phân bổ</span>}
          icon="mark_email_unread" iconBg="bg-[#eff4ff]" iconColor="text-[#004ac6]"
        />
        <StatCard
          label="Đang xử lý" value={loading ? '...' : (stats?.inProgress || 45)}
          sub={<span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#e5eeff] text-[#0051b1] font-semibold">18 kỹ thuật viên</span>}
          icon="autorenew" iconBg="bg-[#e5eeff]" iconColor="text-[#0051b1]"
        />
        <StatCard
          label="Khẩn cấp (P1)" value={loading ? '...' : (stats?.urgent || 6)}
          sub={<span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#ffdad6] text-[#ba1a1a] font-bold">Ưu tiên xử lý ngay</span>}
          icon="warning" iconBg="bg-[#ffdad6]" iconColor="text-[#ba1a1a]" animate
          subColor="text-[#ba1a1a]"
        />
        <StatCard
          label="Đã giải quyết" value={loading ? '...' : (stats?.resolved || 1180)}
          sub={<><span className="text-[#004ac6] font-semibold">91.8%</span> <span className="text-[#565e74]">tổng số vụ</span></>}
          icon="task_alt" iconBg="bg-[#eff4ff]" iconColor="text-[#004ac6]"
        />
        <StatCard
          label="Tuân thủ SLA" value={loading ? '...' : (stats?.slaRate || '98.4%')}
          sub={<><span className="text-[#565e74]">Mục tiêu:</span> <span className="text-[#0b1c30] font-semibold">&gt; 98.0%</span></>}
          icon="verified" iconBg="bg-[#dce9ff]" iconColor="text-[#004ac6]"
          subColor="text-[#004ac6]"
        />
      </div>

      {/* Network Infrastructure Status */}
      <div className="bg-white p-5 rounded-xl shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 gap-2">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-[#004ac6] animate-pulse"></div>
            <h2 className="text-[16px] font-semibold text-[#0b1c30]">Giám Sát Trạng Thái Hạ Tầng Mạng Trực Tiếp</h2>
            <span className="px-2 py-0.5 rounded-full bg-[#eff4ff] font-mono text-[11px] text-[#565e74]">LAN / WAN / SD-WAN Topology</span>
          </div>
          <div className="flex items-center gap-3 text-[13px] text-[#565e74]">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#004ac6]"></span> Ổn định</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#ba1a1a]"></span> Sự cố</span>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <NetworkCard
            icon="hub" label="Core Switch Backbone"
            name="Cisco Catalyst 9500" status="99.98%"
            statusColor="text-[#004ac6] font-semibold"
            detail={
              <div className="w-full bg-[#d3e4fe] h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-[#004ac6] h-full rounded-full" style={{ width: '99.9%' }}></div>
              </div>
            }
          />
          <NetworkCard
            icon="security" label="Tường Lửa Fortinet"
            name="FortiGate 200F Cluster"
            status="Bình thường" statusColor="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[#dce9ff] text-[#004ac6] font-semibold"
            detail={
              <div className="flex items-center justify-between text-[#565e74] font-mono text-[11px] mt-2">
                <span>CPU: 24%</span><span>Sessions: 14.8k</span>
              </div>
            }
          />
          <NetworkCard
            icon="wifi" label="Điểm Truy Cập Wi-Fi"
            name="Aruba AP-535 Mesh" status="142/145 Online"
            detail={
              <div className="w-full bg-[#d3e4fe] h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-[#004ac6] h-full rounded-full" style={{ width: '97.9%' }}></div>
              </div>
            }
          />
          <NetworkCard
            icon="speed" label="Băng Thông WAN 1 & 2"
            name="Tải hiện thời 78%" status="780 Mbps / 1Gbps"
            detail={
              <div className="w-full bg-[#d3e4fe] h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-[#0051b1] h-full rounded-full" style={{ width: '78%' }}></div>
              </div>
            }
          />
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Bar Chart */}
        <div className="lg:col-span-6 bg-white p-5 rounded-xl shadow-sm flex flex-col">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 gap-2">
            <div>
              <h2 className="text-[16px] font-semibold text-[#0b1c30]">Xu Hướng Sự Cố Theo Tháng</h2>
              <p className="text-[13px] text-[#565e74]">Phân loại sự cố mạng so với yêu cầu hỗ trợ thiết bị máy trạm</p>
            </div>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-[#004ac6]"></span> Sự cố mạng</span>
              <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-[#565e74]"></span> Hỗ trợ thiết bị</span>
            </div>
          </div>
          <div className="w-full h-64 pt-3 flex flex-col justify-end">
            <svg className="w-full h-52 overflow-visible" viewBox="0 0 520 180" preserveAspectRatio="none">
              <line className="text-[#dce9ff]" stroke="currentColor" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="520" y1="20" y2="20"/>
              <line className="text-[#dce9ff]" stroke="currentColor" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="520" y1="65" y2="65"/>
              <line className="text-[#dce9ff]" stroke="currentColor" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="520" y1="110" y2="110"/>
              <line className="text-[#dce9ff]" stroke="currentColor" strokeWidth="1" x1="0" x2="520" y1="155" y2="155"/>
              {[
                { x: 25, h1: 85, h2: 60, label: 'T10' },
                { x: 110, h1: 100, h2: 70, label: 'T11' },
                { x: 195, h1: 110, h2: 80, label: 'T12' },
                { x: 280, h1: 95, h2: 75, label: 'T01' },
                { x: 365, h1: 117, h2: 87, label: 'T02' },
                { x: 450, h1: 130, h2: 95, label: 'T03' },
              ].map(({ x, h1, h2, label }) => (
                <g key={label} transform={`translate(${x}, 0)`}>
                  <rect fill="#004ac6" className="hover:opacity-80 transition-opacity" height={h1} rx="3" width="18" x="0" y={155 - h1}/>
                  <rect fill="#565e74" className="hover:opacity-80 transition-opacity" height={h2} rx="3" width="18" x="22" y={155 - h2}/>
                  <text fill="#565e74" fontSize="11" textAnchor="middle" x="20" y="172">{label}</text>
                </g>
              ))}
            </svg>
          </div>
          <div className="mt-3 pt-2 bg-[#eff4ff] p-2 rounded-xl flex items-center justify-between text-[#565e74] font-mono text-[11px]">
            <span>Tổng trung bình: 198 ticket/tháng</span>
            <span className="text-[#004ac6] font-semibold">Tỷ lệ xử lý thành công đúng SLA: 98.4%</span>
          </div>
        </div>

        {/* Donut Chart */}
        <div className="lg:col-span-3 bg-white p-5 rounded-xl shadow-sm flex flex-col">
          <h2 className="text-[16px] font-semibold text-[#0b1c30]">Cơ Cấu Loại Sự Cố</h2>
          <p className="text-[13px] text-[#565e74]">Thống kê phân bổ theo danh mục kỹ thuật</p>
          <div className="relative flex items-center justify-center my-4">
            <svg className="w-44 h-44 -rotate-90 transform" viewBox="0 0 100 100">
              <circle className="stroke-[#dce9ff]" cx="50" cy="50" fill="none" r="38" strokeWidth="12"/>
              <circle className="text-[#004ac6]" cx="50" cy="50" fill="none" r="38" stroke="currentColor" strokeDasharray="238.76" strokeDashoffset="83.56" strokeWidth="12"/>
              <circle cx="50" cy="50" fill="none" r="38" stroke="#0051b1" strokeDasharray="238.76" strokeDashoffset="143.25" strokeWidth="12" style={{ transformOrigin: 'center', transform: 'rotate(126deg)' }}/>
              <circle cx="50" cy="50" fill="none" r="38" stroke="#565e74" strokeDasharray="238.76" strokeDashoffset="195.78" strokeWidth="12" style={{ transformOrigin: 'center', transform: 'rotate(216deg)' }}/>
              <circle cx="50" cy="50" fill="none" r="38" stroke="#737686" strokeDasharray="238.76" strokeDashoffset="210.10" strokeWidth="12" style={{ transformOrigin: 'center', transform: 'rotate(280.8deg)' }}/>
              <circle cx="50" cy="50" fill="none" r="38" stroke="#ba1a1a" strokeDasharray="238.76" strokeDashoffset="214.88" strokeWidth="12" style={{ transformOrigin: 'center', transform: 'rotate(324deg)' }}/>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
              <span className="text-[20px] font-bold text-[#0b1c30]">1,284</span>
              <span className="font-mono text-[11px] text-[#565e74]">Tổng sự cố</span>
            </div>
          </div>
          <div className="space-y-1.5 text-[13px]">
            {[
              { color: 'bg-[#004ac6]', label: 'Mất kết nối Internet', pct: '35%' },
              { color: 'bg-[#0051b1]', label: 'Wi-Fi chập chờn', pct: '25%' },
              { color: 'bg-[#565e74]', label: 'Lỗi máy chủ Server', pct: '18%' },
              { color: 'bg-[#737686]', label: 'Nghẽn băng thông', pct: '12%' },
              { color: 'bg-[#ba1a1a]', label: 'Lỗi Switch / Router', pct: '10%' },
            ].map(({ color, label, pct }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="flex items-center gap-1.5"><span className={`w-2.5 h-2.5 rounded-full ${color}`}></span> {label}</span>
                <span className="font-mono text-[11px] font-semibold text-[#0b1c30]">{pct}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Severity */}
        <div className="lg:col-span-3 bg-white p-5 rounded-xl shadow-sm flex flex-col">
          <h2 className="text-[16px] font-semibold text-[#0b1c30]">Mức Độ Nghiêm Trọng</h2>
          <p className="text-[13px] text-[#565e74]">Tỷ trọng ưu tiên phân bổ nhân sự</p>
          <div className="space-y-4 my-auto py-2">
            <PriorityBar icon="crisis_alert" label="Khẩn cấp (P1)" labelColor="text-[#ba1a1a]" count="6 ticket (4.6%)" pct="14%" barColor="bg-[#ba1a1a]" />
            <PriorityBar icon="priority_high" label="Mức Cao (P2)" labelColor="text-[#0051b1]" count="24 ticket (18.6%)" pct="28%" barColor="bg-[#0051b1]" />
            <PriorityBar icon="drag_handle" label="Mức Trung Bình (P3)" labelColor="text-[#565e74]" count="58 ticket (45.1%)" pct="62%" barColor="bg-[#565e74]" />
            <PriorityBar icon="low_priority" label="Mức Thấp (P4)" labelColor="text-[#434655]" count="41 ticket (31.7%)" pct="48%" barColor="bg-[#c3c6d7]" />
          </div>
          <div className="p-2 bg-[#eff4ff] rounded-xl">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#004ac6] text-[20px]">timer</span>
              <div className="flex flex-col">
                <span className="text-[11px] text-[#0b1c30] font-semibold">Thời gian phản hồi TB (MTTR)</span>
                <span className="font-mono text-[11px] text-[#565e74]">P1: 8 phút | P2: 22 phút | P3: 45 phút</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Emergency Queue Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#eff4ff]/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-[#ffdad6] text-[#ba1a1a] font-mono text-[11px] font-bold uppercase tracking-wider">
                Emergency Queue
              </span>
              <h2 className="text-[16px] font-semibold text-[#0b1c30]">Danh Sách Sự Cố Cần Xử Lý Khẩn Cấp</h2>
            </div>
            <p className="text-[13px] text-[#565e74] mt-0.5">
              Các ticket nghiêm trọng (P1/P2) có nguy cơ ảnh hưởng toàn bộ hạ tầng hoặc trễ cam kết SLA.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] text-[#ba1a1a] font-semibold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#ba1a1a] animate-ping"></span>
              6 Ticket đang chờ giải tỏa
            </span>
            <Link to="/tickets">
              <button className="px-3 py-1.5 rounded-lg bg-[#dce9ff] text-[#004ac6] hover:bg-[#d3e4fe] transition-colors text-[12px] font-semibold">
                Xem Tất Cả Hàng Đợi
              </button>
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#eff4ff] text-[#565e74] text-[11px] font-medium uppercase tracking-wider">
                <th className="py-3 px-3">Mã Ticket</th>
                <th className="py-3 px-3">Tiêu Đề & Chi Tiết Lỗi</th>
                <th className="py-3 px-3">Vị Trí / Khu Vực</th>
                <th className="py-3 px-3">Người Báo Cáo</th>
                <th className="py-3 px-3">Kỹ Thuật Viên Phụ Trách</th>
                <th className="py-3 px-3">Đếm Ngược SLA</th>
                <th className="py-3 px-3 text-right">Thao Tác</th>
              </tr>
            </thead>
            <tbody className="divide-y-0">
              {emergencyTickets.map((t) => (
                <EmergencyRow key={t.id} {...t} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

